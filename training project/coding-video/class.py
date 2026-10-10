
class Player:
    def __init__(self, name):
        self.name = name
        self.health = 100

    def take_damage(self, amount):
        self.health -= amount

    def heal(self, amount):
        self.health += amount

    def show_status(self):
        print(f"{self.name}: {self.health} HP")


player1 = Player("Alex")
player2 = Player("Sam")

player1.take_damage(30)
player2.take_damage(10)
player1.heal(15)

player1.show_status()
player2.show_status()
    