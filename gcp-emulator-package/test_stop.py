from app.services.docker_driver import DockerDriver

driver = DockerDriver()
container_id = '73bae420006c491adccf464df022e8ddf45e81fc2f14ef23991852f7d32206b5'

print(f"Testing stop_container with ID: {container_id[:12]}...")
result = driver.stop_container(container_id)
print(f"Result: {result}")

if result:
    print("✅ Stop succeeded")
else:
    print("❌ Stop failed")
