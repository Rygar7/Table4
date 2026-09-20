import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


FEDERAL_STANDARD_DEDUCTION = 16_100.0
FEDERAL_BRACKETS = [
    (0.0, 0.10),
    (12_400.0, 0.12),
    (50_400.0, 0.22),
    (105_700.0, 0.24),
    (201_775.0, 0.32),
    (256_225.0, 0.35),
    (640_600.0, 0.37),
]
SOCIAL_SECURITY_RATE = 0.062
SOCIAL_SECURITY_WAGE_BASE = 184_500.0
MEDICARE_RATE = 0.0145
ADDITIONAL_MEDICARE_RATE = 0.009
ADDITIONAL_MEDICARE_THRESHOLD = 200_000.0

# 2026 single-filer state brackets and standard deductions compiled by the
# Tax Foundation. This intentionally estimates wage income only; credits,
# exemptions, local taxes, and special recapture rules are not modeled.
STATE_TAX_RULES = {
    "AL": (3000, [(0, .02), (500, .04), (3000, .05)]),
    "AK": (0, []), "AZ": (8350, [(0, .025)]), "AR": (2470, [(0, .02), (4600, .039)]),
    "CA": (5540, [(0, .01), (11079, .02), (26264, .04), (41452, .06), (57542, .08), (72724, .093), (371479, .103), (445771, .113), (742953, .123), (1000000, .133)]),
    "CO": (16100, [(0, .044)]),
    "CT": (0, [(0, .02), (10000, .045), (50000, .055), (100000, .06), (200000, .065), (250000, .069), (500000, .0699)]),
    "DE": (3250, [(2000, .022), (5000, .039), (10000, .048), (20000, .052), (25000, .0555), (60000, .066)]),
    "FL": (0, []), "GA": (12000, [(0, .0519)]),
    "HI": (4400, [(0, .014), (9600, .032), (14400, .055), (19200, .064), (24000, .068), (36000, .072), (48000, .076), (125000, .079), (175000, .0825), (225000, .09), (275000, .10), (325000, .11)]),
    "ID": (16100, [(4811, .053)]), "IL": (0, [(0, .0495)]), "IN": (0, [(0, .0295)]),
    "IA": (16100, [(0, .038)]), "KS": (3605, [(0, .052), (23000, .0558)]),
    "KY": (3360, [(0, .035)]), "LA": (12875, [(0, .03)]),
    "ME": (8350, [(0, .058), (27399, .0675), (64849, .0715)]),
    "MD": (3350, [(0, .02), (1000, .03), (2000, .04), (3000, .0475), (100000, .05), (125000, .0525), (150000, .055), (250000, .0575), (500000, .0625), (1000000, .065)]),
    "MA": (0, [(0, .05), (1083150, .09)]), "MI": (0, [(0, .0425)]),
    "MN": (15300, [(0, .0535), (33310, .068), (109430, .0785), (203150, .0985)]),
    "MS": (2300, [(10000, .04)]),
    "MO": (16100, [(1348, .02), (2696, .025), (4044, .03), (5392, .035), (6740, .04), (8088, .045), (9436, .047)]),
    "MT": (16100, [(0, .047), (47500, .0565)]),
    "NE": (8850, [(0, .0246), (4130, .0351), (24760, .0455)]),
    "NV": (0, []), "NH": (0, []),
    "NJ": (0, [(0, .014), (20000, .0175), (35000, .035), (40000, .05525), (75000, .0637), (500000, .0897), (1000000, .1075)]),
    "NM": (16100, [(0, .015), (5500, .032), (16500, .043), (33500, .047), (66500, .049), (210000, .059)]),
    "NY": (8000, [(0, .039), (8500, .044), (11700, .0515), (13900, .054), (80650, .059), (215400, .0685), (1077550, .0965), (5000000, .103), (25000000, .109)]),
    "NC": (12750, [(0, .0399)]), "ND": (16100, [(48475, .0195), (244825, .025)]),
    "OH": (0, [(26050, .0275)]), "OK": (6350, [(3750, .025), (4900, .035), (7200, .045)]),
    "OR": (2910, [(0, .0475), (4550, .0675), (11400, .0875), (125000, .099)]),
    "PA": (0, [(0, .0307)]), "RI": (11200, [(0, .0375), (82050, .0475), (186450, .0599)]),
    "SC": (8350, [(0, 0), (3640, .03), (18230, .06)]),
    "SD": (0, []), "TN": (0, []), "TX": (0, []), "UT": (0, [(0, .045)]),
    "VT": (7650, [(0, .0335), (49400, .066), (119700, .076), (249700, .0875)]),
    "VA": (8750, [(0, .02), (3000, .03), (5000, .05), (17000, .0575)]),
    "WA": (0, []),
    "WV": (0, [(0, .0222), (10000, .0296), (25000, .0333), (40000, .0444), (60000, .0482)]),
    "WI": (13960, [(0, .035), (15110, .044), (51950, .053), (332720, .0765)]),
    "WY": (0, []),
    "DC": (16100, [(0, .04), (10000, .06), (40000, .065), (60000, .085), (250000, .0925), (500000, .0975), (1000000, .1075)]),
}


class TaxLookupError(ValueError):
    pass


def progressive_tax(taxable_income: float, brackets: list[tuple[float, float]]) -> float:
    tax = 0.0
    for index, (threshold, rate) in enumerate(brackets):
        if taxable_income <= threshold:
            break
        ceiling = brackets[index + 1][0] if index + 1 < len(brackets) else taxable_income
        tax += max(0.0, min(taxable_income, ceiling) - threshold) * rate
    return tax


def lookup_zip(zip_code: str) -> tuple[str, str]:
    request = Request(
        f"https://api.zippopotam.us/us/{zip_code}",
        headers={"User-Agent": "LifePath-AI/1.0"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise TaxLookupError("We could not identify that ZIP code. Check it and try again.") from exc
    places = data.get("places") or []
    if not places:
        raise TaxLookupError("We could not identify that ZIP code. Check it and try again.")
    state_code = places[0].get("state abbreviation")
    if state_code not in STATE_TAX_RULES:
        raise TaxLookupError("State tax information is unavailable for that ZIP code.")
    return places[0].get("state", state_code), state_code


def estimate_taxes(monthly_gross: float, state_code: str) -> dict[str, float]:
    annual_gross = monthly_gross * 12
    federal_taxable = max(0.0, annual_gross - FEDERAL_STANDARD_DEDUCTION)
    federal = progressive_tax(federal_taxable, FEDERAL_BRACKETS)
    state_deduction, state_brackets = STATE_TAX_RULES[state_code]
    state_taxable = max(0.0, annual_gross - state_deduction)
    state = progressive_tax(state_taxable, state_brackets)
    payroll = (
        min(annual_gross, SOCIAL_SECURITY_WAGE_BASE) * SOCIAL_SECURITY_RATE
        + annual_gross * MEDICARE_RATE
        + max(0.0, annual_gross - ADDITIONAL_MEDICARE_THRESHOLD) * ADDITIONAL_MEDICARE_RATE
    )
    return {"federal": federal, "state": state, "payroll": payroll}
