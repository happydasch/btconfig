import btconfig
btconfig.PATH_STRATEGY.extend(['simple_strategy'])

if __name__ == '__main__':
    res = btconfig.run(btconfig.MODE_OPTIMIZEGENETIC, "config.json")
