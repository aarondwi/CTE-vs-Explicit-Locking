class Room:
  def __init__(self, id, name, val):
    super().__init__()
    self.id = id
    self.name = name
    self.val = val

  def save(self):
    print("Record is saved! The values are")
    print(f"id: {self.id}")
    print(f"name: {self.name}")
    print(f"val: {self.val}")

def getRoomById(id):
  return Room(id, 'random_name', 10)

if __name__ == "__main__":
  room = getRoomById(1)
  room.val += 5
  room.save()