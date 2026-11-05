import math
import random
from models import Request


class Device:

  def __init__(self, did, mu):
    self.did, self.mu, self.busy, self.req, self.rel = did, mu, False, None, float("inf")

  def start(self, req: Request, t: float):
    self.busy, self.req = True, req
    self.rel = t + (-math.log(1.0 - random.random()) / self.mu)
    return self.rel

  def release(self):
    self.busy, r, self.req, self.rel = False, self.req, None, float("inf")
    return r