import threading
import os
import pickle

from cache import DnsCache

cache_filename = 'cache'


# region Commands
def save_cache(server):
    server.save_cache(cache_filename)
    print('Cache saved')

def stop_server(server):
    server.running = False
    print('Server stopping...')
    server.join()
    # TODO: join threads by reference
    for thread in threading.enumerate():
        if thread != threading.main_thread():
            thread.join()
    server.stop()
    print('Server stopped')
    server.save_cache(cache_filename)
    print('And cache saved')

def show_cache(server):
    print('Cache status:')
    print(server.cache.get_status())

def toggle_server(server):
    server.forwarding = flag = not server.forwarding
    print(f'Working: {flag}')

def clear(server):
    server.cache.clear()

commands = {
    'save': save_cache,
    'stop': stop_server,
    'cache': show_cache,
    'toggle': toggle_server,
    'clear': clear
}
# endregion

def get_cache():
    if os.path.exists(cache_filename) and os.path.getsize(cache_filename) > 0:
        with open(cache_filename, 'rb') as file:
            return pickle.load(file)
    else:
        return DnsCache()

def print_help():
    coms = '\n'.join(map(lambda c: '  '+str(c), commands))
    lines = f'Server commands:\n{coms}'
    print(lines)

def main():
    from server import DnsServer
    server = DnsServer()
    server.cache = get_cache()
    server.start()
    print('Server started')
    print_help()
    while server.running:
        command = input()
        if command in commands:
            commands[command](server)
        elif command == 'help':
            print_help()
        else:
            print('> Unknown command')

if __name__ == '__main__':
    main()
