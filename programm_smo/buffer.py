from models import Request


class Buffer:

  def __init__(self, cap):
    self.cap = cap
    self.slots = [None] * cap

  def has_free(self):
    return any(s is None for s in self.slots)

  def is_empty(self):
    return all(s is None for s in self.slots)

  def put(self, req):
    for i in range(self.cap):
      if self.slots[i] is None:
        self.slots[i] = req
        return i
    return -1

  def pop_oldest(self):
    idx, oldest = -1, None
    for i in range(self.cap):
      if self.slots[i] and (oldest is None or self.slots[i].gtime < oldest.gtime):
        oldest, idx = self.slots[i], i
    if idx != -1:
      self.slots[idx] = None
    return idx, oldest

  def pop_priority(self):
    idx, best = -1, None
    for i in range(self.cap):
      r = self.slots[i]
      if r:
        if best is None or r.sid < best.sid or (r.sid == best.sid and r.gtime < best.gtime):
          best, idx = r, i
    if idx != -1:
      self.slots[idx] = None
    return idx, best