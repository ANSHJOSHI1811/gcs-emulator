import docker

client = docker.from_env()
c = client.containers.get('73bae420006c')
print(f'Container state: {c.status}')
c.stop(timeout=5)
print('Stopped successfully')
c.reload()
print(f'After stop: {c.status}')
c.start()
print('Started successfully')
c.reload()
print(f'After start: {c.status}')
