from UserApp import UserApp
from AdminApp import MapManager
from simulation import MapApp

if __name__ == '__main__':
    admin = False
    if admin:
        MapManager().run()
    else:
        # UserApp().run()
        MapApp.run()

