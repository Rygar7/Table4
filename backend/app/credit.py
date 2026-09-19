from .models import CardUtilization, CreditMetrics, CreditProfile


def analyze_credit(profile: CreditProfile) -> CreditMetrics:
    total_card_balance = sum(card.balance for card in profile.credit_cards)
    total_credit_limit = sum(card.credit_limit for card in profile.credit_cards)
    overall_utilization = (
        round(total_card_balance / total_credit_limit * 100, 1)
        if total_credit_limit
        else None
    )
    high_utilization_cards = [
        CardUtilization(
            name=card.name,
            utilization_percent=round(card.balance / card.credit_limit * 100, 1),
        )
        for card in profile.credit_cards
        if card.balance / card.credit_limit >= 0.3
    ]
    return CreditMetrics(
        total_card_balance=round(total_card_balance, 2),
        total_credit_limit=round(total_credit_limit, 2),
        overall_utilization_percent=overall_utilization,
        high_utilization_cards=high_utilization_cards,
        missed_payments_12_months=sum(
            card.missed_payments_12_months for card in profile.credit_cards
        ),
        total_loan_balance=round(sum(loan.balance for loan in profile.loans), 2),
        monthly_debt_payments=round(
            sum(card.minimum_payment for card in profile.credit_cards)
            + sum(loan.monthly_payment for loan in profile.loans),
            2,
        ),
        available_cash=round(sum(account.balance for account in profile.bank_accounts), 2),
    )
