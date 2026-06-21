import random
import json
import csv
import os
from collections import deque

import analytical


class MM1Simulator:
    def __init__(self, lambda_, mu, sim_duration=5000, warmup_time=500, seed=None, save_events=False):
        self.lambda_ = lambda_
        self.mu = mu
        self.sim_duration = sim_duration
        self.warmup_time = warmup_time
        self.save_events = save_events
        if seed is not None:
            random.seed(seed)
        self.reset()

    def reset(self):
        self.current_time = 0.0
        self.next_arrival_time = random.expovariate(self.lambda_)
        self.next_departure_time = float('inf')
        self.server_busy = False
        self.queue = deque()
        self.current_service_arrival = None
        self.time_last_event = 0.0

        self._recording = False

        self.total_area_L = 0.0
        self.total_area_Lq = 0.0
        self.total_busy_time = 0.0
        self.wait_times = []
        self.wait_times_queue = []
        self.n_arrivals = 0
        self.n_departures = 0
        self.n_in_system_at_arrival = []
        self.events = []

    def _n_in_system(self):
        return len(self.queue) + (1 if self.server_busy else 0)

    def _accumulate_areas(self):
        dt = self.current_time - self.time_last_event
        if dt > 0 and self._recording:
            n = self._n_in_system()
            self.total_area_L += n * dt
            self.total_area_Lq += len(self.queue) * dt
            if self.server_busy:
                self.total_busy_time += dt

    def _handle_arrival(self):
        n_before = self._n_in_system()
        self.n_arrivals += 1
        if self._recording:
            self.n_in_system_at_arrival.append(n_before)

        if not self.server_busy:
            self.server_busy = True
            self.current_service_arrival = self.current_time
            if self._recording:
                self.wait_times_queue.append(0.0)
            service_time = random.expovariate(self.mu)
            self.next_departure_time = self.current_time + service_time
        else:
            self.queue.append(self.current_time)

        self.next_arrival_time = self.current_time + random.expovariate(self.lambda_)

        if self.save_events:
            self.events.append({
                'time': self.current_time,
                'type': 'arrival',
                'n_in_system': self._n_in_system(),
                'queue_len': len(self.queue),
            })

    def _handle_departure(self):
        if self.current_service_arrival is not None and self._recording:
            w = self.current_time - self.current_service_arrival
            self.wait_times.append(w)

        self.n_departures += 1

        if self.queue:
            next_arrival = self.queue.popleft()
            self.current_service_arrival = next_arrival
            if self._recording:
                wq = self.current_time - next_arrival
                self.wait_times_queue.append(wq)
            service_time = random.expovariate(self.mu)
            self.next_departure_time = self.current_time + service_time
        else:
            self.server_busy = False
            self.current_service_arrival = None
            self.next_departure_time = float('inf')

        if self.save_events:
            self.events.append({
                'time': self.current_time,
                'type': 'departure',
                'n_in_system': self._n_in_system(),
                'queue_len': len(self.queue),
            })

    def run(self):
        self.reset()

        while self.current_time < self.sim_duration:
            if self.next_arrival_time <= self.next_departure_time:
                self.current_time = self.next_arrival_time
            else:
                self.current_time = self.next_departure_time

            if self.current_time >= self.warmup_time and not self._recording:
                self._recording = True
                self.total_area_L = 0.0
                self.total_area_Lq = 0.0
                self.total_busy_time = 0.0
                self.wait_times = []
                self.wait_times_queue = []
                self.n_arrivals = 0
                self.n_departures = 0
                self.n_in_system_at_arrival = []

            if self.current_time >= self.sim_duration:
                break

            self._accumulate_areas()

            if self.next_arrival_time <= self.next_departure_time:
                self._handle_arrival()
            else:
                self._handle_departure()

            self.time_last_event = self.current_time

        self._accumulate_areas()
        return self._compute_stats()

    def _compute_stats(self):
        record_time = self.sim_duration - self.warmup_time
        if record_time <= 0 or self.n_departures == 0:
            return {
                'L': 0.0, 'Lq': 0.0, 'W': 0.0, 'Wq': 0.0,
                'rho': 0.0, 'P_idle': 1.0,
                'n_arrivals': 0, 'n_departures': 0,
                'Pn_hist': {}
            }

        L_est = self.total_area_L / record_time
        Lq_est = self.total_area_Lq / record_time
        W_est = sum(self.wait_times) / len(self.wait_times) if self.wait_times else 0.0
        Wq_est = sum(self.wait_times_queue) / len(self.wait_times_queue) if self.wait_times_queue else 0.0
        rho_est = self.total_busy_time / record_time
        P_idle_est = 1.0 - rho_est

        if self.n_in_system_at_arrival:
            max_n = max(self.n_in_system_at_arrival)
            hist = [0] * (max_n + 1)
            for n in self.n_in_system_at_arrival:
                hist[n] += 1
            total = len(self.n_in_system_at_arrival)
            Pn_hist = {str(i): c / total for i, c in enumerate(hist)}
        else:
            Pn_hist = {}

        return {
            'L': L_est,
            'Lq': Lq_est,
            'W': W_est,
            'Wq': Wq_est,
            'rho': rho_est,
            'P_idle': P_idle_est,
            'n_arrivals': self.n_arrivals,
            'n_departures': self.n_departures,
            'Pn_hist': Pn_hist,
        }

    def get_wait_times(self):
        return self.wait_times

    def get_wait_times_queue(self):
        return self.wait_times_queue


def run_experiment(config_path='config.json'):
    with open(config_path, 'r') as f:
        cfg = json.load(f)

    sim_cfg = cfg['simulation']
    cost_cfg = cfg['costs']

    service_time_min = sim_cfg['service_time_minutes_mean']
    mu = 60.0 / service_time_min

    sim_hours = sim_cfg['sim_hours']
    warmup_hours = sim_cfg['warmup_hours']
    seed = sim_cfg.get('random_seed')
    save_events = sim_cfg.get('save_events', False)

    cashier_wage = cost_cfg['cashier_hourly_wage']
    waiting_cost = cost_cfg['customer_waiting_cost_per_hour']

    results = []

    for rho_target in sim_cfg['rho_values']:
        lambda_target = rho_target * mu

        if rho_target >= 0.95:
            actual_sim_hours = 20000
            actual_warmup = 2000
        elif rho_target >= 0.9:
            actual_sim_hours = 10000
            actual_warmup = 1000
        else:
            actual_sim_hours = sim_hours
            actual_warmup = warmup_hours

        sim = MM1Simulator(
            lambda_=lambda_target,
            mu=mu,
            sim_duration=actual_sim_hours,
            warmup_time=actual_warmup,
            seed=seed,
            save_events=save_events,
        )
        stats = sim.run()

        L_ana = analytical.L(rho_target)
        Lq_ana = analytical.Lq(rho_target)
        W_ana = analytical.W(rho_target, mu)
        Wq_ana = analytical.Wq(rho_target, mu)
        P_idle_ana = analytical.P_idle(rho_target)

        cost_sim = cashier_wage + waiting_cost * stats['L']
        cost_ana = cashier_wage + waiting_cost * L_ana

        results.append({
            'rho': rho_target,
            'lambda': lambda_target,
            'mu': mu,
            'L_sim': stats['L'],
            'L_ana': L_ana,
            'Lq_sim': stats['Lq'],
            'Lq_ana': Lq_ana,
            'W_sim_hours': stats['W'],
            'W_ana_hours': W_ana,
            'Wq_sim_hours': stats['Wq'],
            'Wq_ana_hours': Wq_ana,
            'rho_est': stats['rho'],
            'P_idle_sim': stats['P_idle'],
            'P_idle_ana': P_idle_ana,
            'cost_sim_per_hour': cost_sim,
            'cost_ana_per_hour': cost_ana,
            **{f'Pn_sim_{k}': v for k, v in stats['Pn_hist'].items()},
            **{f'Pn_ana_{k}': analytical.Pn(rho_target, int(k)) for k in stats['Pn_hist'].keys()},
        })

        print(f"rho={rho_target:.2f}  L_sim={stats['L']:.4f}  L_ana={L_ana:.4f}  "
              f"Wq_sim={stats['Wq']*60:.2f}min  Wq_ana={Wq_ana*60:.2f}min  "
              f"rho_est={stats['rho']:.4f}")

    os.makedirs('output', exist_ok=True)

    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    fieldnames = sorted(all_keys)

    with open('output/summary.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    return results


if __name__ == '__main__':
    run_experiment('config.json')
