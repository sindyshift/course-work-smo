from buffer import Buffer
from device import Device
from models import Request
from source import Source


class SimulationModel:

  def __init__(self, ns, bc, nd, a, b, mu):
    self.sources = [Source(i + 1, a, b) for i in range(ns)]
    self.buffer = Buffer(bc)
    self.devices = [Device(i + 1, mu) for i in range(nd)]
    self.t, self.rc, self.ptr = 0.0, 0, 0
    self.rej = self.proc = 0
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
        desc = f"Ген {req} -> Отказ (выбит {victim} из [{oidx}]), занял [{idx}]"

      self._assign()
    elif etype == "REL":
      dev = self.devices[oid - 1]
      done = dev.release()
      self.proc += 1
      desc = f"Прибор П{dev.did} освободился ({done} готов)"
      self._assign()

    self._print(step_n, desc)

  def _assign(self):
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

  def _print(self, n, desc):
    buf_view = [str(s) if s else "_" for s in self.buffer.slots]
    dev_view = [f"П{d.did}:({d.req if d.busy else 'свободен'})" for d in self.devices]
    print(f"[{n:02d}] t={self.t:.2f} | Событие: {desc}")
    print(f"     Буфер: {buf_view} | Приборы: {dev_view} | Отказы: {self.rej}, Ок: {self.proc}\n")