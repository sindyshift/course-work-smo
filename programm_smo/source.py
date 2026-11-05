import random


class Source:

  def __init__(self, sid, a, b):
    self.sid, self.a, self.b, self.next_t = sid, a, b, 0.0

  def next_time(self, t):
    self.next_t = t + random.uniform(self.a, self.b)
    return self.next_t