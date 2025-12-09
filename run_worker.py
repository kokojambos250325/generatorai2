import asyncio
from workers.worker import Worker


async def main():
    """
    Точка входа для запуска воркера
    
    Создаёт экземпляр Worker и запускает его основной цикл обработки задач.
    """
    print("Starting worker...")
    
    # Создание воркера
    worker = Worker(poll_interval=5)
    
    try:
        # Запуск цикла обработки
        await worker.start_loop()
    except KeyboardInterrupt:
        print("\nShutting down worker...")
        await worker.stop()
    except Exception as e:
        print(f"Worker error: {e}")
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
