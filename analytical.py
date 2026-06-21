import math


def rho_from_lambda_mu(lambda_, mu):
    return lambda_ / mu


def L(rho):
    if rho >= 1:
        return float('inf')
    return rho / (1 - rho)


def Lq(rho):
    if rho >= 1:
        return float('inf')
    return rho**2 / (1 - rho)


def W(rho, mu):
    if rho >= 1:
        return float('inf')
    return 1 / (mu * (1 - rho))


def Wq(rho, mu):
    if rho >= 1:
        return float('inf')
    return rho / (mu * (1 - rho))


def Pn(rho, n):
    if rho >= 1:
        return 0
    return (1 - rho) * (rho ** n)


def P_idle(rho):
    return 1 - rho if rho < 1 else 0


def P_wait_gt(rho, mu, t):
    if rho >= 1:
        return 1.0
    return rho * math.exp(-mu * (1 - rho) * t)


def P_wait_in_queue(rho):
    return rho


def cost_analytical(rho, mu, lambda_, cashier_wage, waiting_cost):
    L_val = L(rho)
    return cashier_wage + waiting_cost * L_val
