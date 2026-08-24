def calculate_emi(principal, annual_rate, years):
    if principal <= 0:
        raise ValueError("Loan amount must be greater than zero.")

    if years <= 0:
        raise ValueError("Loan tenure must be greater than zero.")

    if annual_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    months = years * 12

    if annual_rate == 0:
        emi = principal / months
        return round(emi, 2), 0.00, round(principal, 2)

    monthly_rate = annual_rate / (12 * 100)
    emi = (
        principal
        * monthly_rate
        * (1 + monthly_rate) ** months
    ) / ((1 + monthly_rate) ** months - 1)

    total = emi * months
    interest = total - principal

    return round(emi, 2), round(interest, 2), round(total, 2)
