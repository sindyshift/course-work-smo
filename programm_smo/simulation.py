import math
from buffer import Buffer
from device import Device
from models import Request
from source import Source


class SimulationModel:

  def __init__(self, ns, bc, nd, a, b, mu):
    self.ns = ns
    self.bc = bc
    self.nd = nd
    self.a = a
    self.b = b
    self.mu = mu

    # Поля для пошагового режима (ОД2)
    self.sources = [Source(i + 1, a, b) for i in range(ns)]
    self.buffer = Buffer(bc)
    self.devices = [Device(i + 1, mu) for i in range(nd)]
    self.t = 0.0
    self.rc = 0
    self.ptr = 0
    self.rej = 0
    self.proc = 0
    for s in self.sources:
      s.next_time(self.t)

  def step(self, step_n):
    min_t, etype, oid = float("inf"), "", -1
    for s in self.sources:
      if s.next_t < min_t:
        min_t, etype, oid = s.next_t, "GEN", s.sid
    for d in self.devices:
      if d.busy and d.rel < min_t:
        min_t, etype, oid = d.rel, "REL", d.did

    self.t = min_t
    desc = ""

    if etype == "GEN":
      src = self.sources[oid - 1]
      self.rc += 1
      req = Request(self.rc, src.sid, self.t)
      src.next_time(self.t)

      if self.buffer.has_free():
        idx = self.buffer.put(req)
        desc = f"Ген {req} -> Буфер [{idx}]"
      else:
        oidx, victim = self.buffer.pop_oldest()
        self.rej += 1
        idx = self.buffer.put(req)
        desc = (
            f"Ген {req} -> Отказ (выбит {victim} из [{oidx}]), занял [{idx}]"
        )

      self._assign_step()
    elif etype == "REL":
      dev = self.devices[oid - 1]
      done, _ = dev.release()
      self.proc += 1
      desc = f"Прибор П{dev.did} освободился ({done} готов)"
      self._assign_step()

    self._print_step(step_n, desc)

  def _assign_step(self):
    if self.buffer.is_empty():
      return
    start = self.ptr
    dev = None
    for i in range(len(self.devices)):
      idx = (start + i) % len(self.devices)
      if not self.devices[idx].busy:
        dev = self.devices[idx]
        self.ptr = (idx + 1) % len(self.devices)
        break
    if dev:
      _, req = self.buffer.pop_priority()
      if req:
        dev.start(req, self.t)

  def _print_step(self, n, desc):
    buf_view = [str(s) if s else "_" for s in self.buffer.slots]
    dev_view = [
        f"П{d.did}:({d.req if d.busy else 'свободен'})" for d in self.devices
    ]
    print(f"[{n:02d}] t={self.t:.2f} | Событие: {desc}")
    print(
        f"     Буфер: {buf_view} | Приборы: {dev_view} | Отказы: {self.rej},"
        f" Ок: {self.proc}\n"
    )

  def _run_simulation(self, max_generated_requests):
    sources = [Source(i + 1, self.a, self.b) for i in range(self.ns)]
    buffer = Buffer(self.bc)
    devices = [Device(i + 1, self.mu) for i in range(self.nd)]

    t = 0.0
    rc = 0
    ptr = 0
    generated_total = 0

    source_stats = {
        i + 1: {
            "gen": 0,
            "rej": 0,
            "wait": [],
            "service": [],
            "full": [],
        }
        for i in range(self.ns)
    }

    for s in sources:
      s.next_time(t)

    while True:
      min_t, etype, oid = float("inf"), "", -1

      if generated_total < max_generated_requests:
        for s in sources:
          if s.next_t < min_t:
            min_t, etype, oid = s.next_t, "GEN", s.sid

      for d in devices:
        if d.busy and d.rel < min_t:
          min_t, etype, oid = d.rel, "REL", d.did

      if min_t == float("inf"):
        break

      t = min_t

      if etype == "GEN":
        src = sources[oid - 1]
        rc += 1
        generated_total += 1
        source_stats[src.sid]["gen"] += 1

        req = Request(rc, src.sid, t)
        src.next_time(t)

        if buffer.has_free():
          buffer.put(req)
        else:
          _, victim = buffer.pop_oldest()
          if victim:
            source_stats[victim.sid]["rej"] += 1
            wait_t = t - victim.gtime
            source_stats[victim.sid]["wait"].append(wait_t)
            source_stats[victim.sid]["full"].append(wait_t)
          buffer.put(req)

        self._assign_auto(buffer, devices, ptr, t)

      elif etype == "REL":
        dev = devices[oid - 1]
        req, service_duration = dev.release()

        if req:
          sid = req.sid
          wait_time = dev.start_time - req.gtime
          full_time = t - req.gtime

          source_stats[sid]["wait"].append(wait_time)
          source_stats[sid]["service"].append(service_duration)
          source_stats[sid]["full"].append(full_time)

        self._assign_auto(buffer, devices, ptr, t)

    total_time = t if t > 0 else 1.0
    device_load = {d.did: d.total_busy_time / total_time for d in devices}

    return source_stats, device_load, total_time

  def _assign_auto(self, buffer, devices, ptr, t):
    if buffer.is_empty():
      return
    for i in range(len(devices)):
      idx = (ptr + i) % len(devices)
      if not devices[idx].busy:
        dev = devices[idx]
        _, req = buffer.pop_priority()
        if req:
          dev.start(req, t)
          break

  def run_automatic_mode(self):
    print(
        "--- ЗАПУСК АВТОМАТИЧЕСКОГО РЕЖИМА С ИТЕРАЦИОННЫМ РАСЧЕТОМ N ---"
    )
    t_alpha = 1.643
    delta = 0.1

    N = 100
    iteration = 1
    p_prev = -1.0

    while True:
      source_stats, device_load, total_time = self._run_simulation(N)

      total_gen = sum(st["gen"] for st in source_stats.values())
      total_rej = sum(st["rej"] for st in source_stats.values())
      p_curr = total_rej / total_gen if total_gen > 0 else 0.0001
      if p_curr == 0:
        p_curr = 0.0001

      N_new = int((t_alpha**2 * (1.0 - p_curr)) / (p_curr * (delta**2)))
      if N_new < 100:
        N_new = 100

      print(
          f"Итерация {iteration}: N = {N}, Вероятность отказа p = {p_curr:.5f},"
          f" Расчетное N_new = {N_new}"
      )

      if iteration > 1 and abs(p_prev - p_curr) < (0.1 * p_prev):
        print(f"-> Требуемая точность достигнута на итерации {iteration}!\n")
        N = N_new
        break

      p_prev = p_curr
      N = N_new
      iteration += 1
      if iteration > 20:
        break

    source_stats, device_load, total_time = self._run_simulation(N)
    self._print_final_report(source_stats, device_load, N)

  def _print_final_report(self, source_stats, device_load, N):
    print("==================================================")
    print(f" ИТОГОВЫЕ РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ (Автоматический режим OP1)")
    print(f" Оптимальное число сгенерированных заявок N = {N}")
    print("==================================================")
    print(
        "Таблица 1: Характеристики источников ВС"
        "\n--------------------------------------------------------------------------------"
    )
    print(
        f"{'Источник':<10} | {'Кол-во заявок':<13} | {'p_отк':<8} |"
        f" {'T_преб':<8} | {'T_БП':<8} | {'T_обсл':<8} | {'D_БП':<8}"
    )
    print("-" * 80)

    for sid, st in source_stats.items():
      gen = st["gen"]
      rej = st["rej"]
      p_otk = rej / gen if gen > 0 else 0.0

      waits = st["wait"]
      services = st["service"]
      fulls = st["full"]

      t_preb = sum(fulls) / len(fulls) if fulls else 0.0
      t_bp = sum(waits) / len(waits) if waits else 0.0
      t_obs = sum(services) / len(services) if services else 0.0

      d_bp = (
          sum((w - t_bp) ** 2 for w in waits) / len(waits)
          if len(waits) > 1
          else 0.0
      )

      print(
          f"И{sid:<9} | {gen:<13} | {p_otk:<8.4f} | {t_preb:<8.4f} |"
          f" {t_bp:<8.4f} | {t_obs:<8.4f} | {d_bp:<8.4f}"
      )

    print(
        "--------------------------------------------------------------------------------\n"
    )
    print(
        "Таблица 2: Характеристики приборов ВС"
        "\n----------------------------------------"
    )
    print(f"{'Прибор':<10} | {'Коэффициент использования (K_исп)':<30}")
    print("-" * 45)
    for did, k_isp in device_load.items():
      print(f"П{did:<9} | {k_isp:<30.4f}")
    print("----------------------------------------\n")