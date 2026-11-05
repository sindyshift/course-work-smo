class Request:

  def __init__(self, rid, sid, gtime):
    self.rid, self.sid, self.gtime = rid, sid, gtime

  def __repr__(self):
    return f"#{self.rid}(И{self.sid})"