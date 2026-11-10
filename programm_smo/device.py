import math
import random


class Device:

  def __init__(self, did, mu):
    self.did = did
    self.mu = mu
    self.busy = False
    self.req = None
    self.rel = float("inf")
    self.start_time = 0.0
    self.total_busy_time = 0.0

  def start(self, req, t: float):
    self.busy = True
    self.req = req
    self.start_time = t
    service_duration = -math.log(1.0 - random.random()) / self.mu
    self.total_busy_time += service_duration
    self.rel = t + service_duration
    return self.rel

  def release(self):
    self.busy = False
    req = self.req
    self.req = None
    service_duration = self.rel - self.start_time
    self.rel = float("inf")
    return req, service_duration