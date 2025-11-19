"""
FastAPI service for casino transaction generation
"""
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import threading
import time
from producers import run_kafka_producer
from config import KAFKA_BOOTSTRAP_SERVERS, EVENTS_PER_SECOND

app = FastAPI(title="Casino Transaction Generator API")

# Global state for generator control
generator_state = {
    "running": False,
    "thread": None,
    "rate": EVENTS_PER_SECOND,
    "stop_flag": False
}


class GeneratorConfig(BaseModel):
    rate: Optional[int] = EVENTS_PER_SECOND
    broker: Optional[str] = KAFKA_BOOTSTRAP_SERVERS


class GeneratorStatus(BaseModel):
    running: bool
    rate: int
    broker: str


def run_generator_thread(broker: str):
    """Run the generator in a background thread with dynamic rate control"""
    generator_state["stop_flag"] = False
    generator_state["running"] = True

    try:
        from kafka import KafkaProducer
        from casino_simulator import CasinoSimulator
        import json

        producer = KafkaProducer(
            bootstrap_servers=broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all'
        )

        simulator = CasinoSimulator()

        while not generator_state["stop_flag"]:
            # Use current rate from state (can be changed dynamically)
            current_rate = generator_state["rate"]

            transactions = simulator.generate_bet()
            for transaction in transactions:
                producer.send('gaming-transactions', value=transaction)
                print(f"[{current_rate} evt/s] {transaction['member_name']} - {transaction['transaction_type']} ${transaction['amount']:.2f}")

            time.sleep(1.0 / current_rate)

        producer.flush()
        producer.close()

    except Exception as e:
        print(f"Generator error: {e}")
    finally:
        generator_state["running"] = False


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Casino Transaction Generator",
        "version": "2.0",
        "endpoints": {
            "GET /status": "Check generator status",
            "GET /rate": "Get current event generation rate",
            "GET /rate/{rate}": "Set rate with simple GET (e.g., /rate/10)",
            "PATCH /rate": "Update event generation rate (JSON body)",
            "POST /start": "Start generating transactions",
            "POST /stop": "Stop generating transactions",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/status", response_model=GeneratorStatus)
async def get_status():
    """Get current generator status"""
    # Convert list to string for broker
    broker_str = KAFKA_BOOTSTRAP_SERVERS[0] if isinstance(KAFKA_BOOTSTRAP_SERVERS, list) else KAFKA_BOOTSTRAP_SERVERS
    return GeneratorStatus(
        running=generator_state["running"],
        rate=generator_state["rate"],
        broker=broker_str
    )


@app.post("/start")
async def start_generator():
    """Start the transaction generator (always runs at default rate of 5 events/sec)"""
    if generator_state["running"]:
        return {
            "status": "already_running",
            "message": "Generator is already running. Use PATCH /rate to change frequency.",
            "rate": generator_state["rate"]
        }

    # Always start at default rate
    rate = EVENTS_PER_SECOND
    broker = KAFKA_BOOTSTRAP_SERVERS[0] if isinstance(KAFKA_BOOTSTRAP_SERVERS, list) else KAFKA_BOOTSTRAP_SERVERS

    generator_state["rate"] = rate

    # Start generator in background thread
    thread = threading.Thread(
        target=run_generator_thread,
        args=(broker,),
        daemon=True
    )
    thread.start()
    generator_state["thread"] = thread

    return {
        "status": "started",
        "message": f"Generator started at {rate} events/sec (use PATCH /rate to change)",
        "rate": rate,
        "broker": broker
    }


@app.get("/rate")
async def get_rate():
    """Get the current event generation rate"""
    return {
        "rate": generator_state["rate"],
        "unit": "events/sec",
        "running": generator_state["running"]
    }


@app.get("/rate/{new_rate}")
async def set_rate_simple(new_rate: int):
    """Set the event generation rate with a simple GET request (e.g., curl http://localhost:8000/rate/10)"""
    if not generator_state["running"]:
        return {
            "status": "not_running",
            "message": "Generator is not running. Start it first with /start",
            "rate": generator_state["rate"]
        }

    old_rate = generator_state["rate"]

    # Update the rate (will take effect on next iteration)
    generator_state["rate"] = new_rate

    return {
        "status": "rate_updated",
        "message": f"Rate changed from {old_rate} to {new_rate} events/sec",
        "old_rate": old_rate,
        "new_rate": new_rate
    }


@app.patch("/rate")
async def update_rate(config: GeneratorConfig):
    """Update the event generation rate (increase or decrease) using JSON body"""
    if not generator_state["running"]:
        return {
            "status": "not_running",
            "message": "Generator is not running. Start it first with /start",
            "rate": generator_state["rate"]
        }

    old_rate = generator_state["rate"]
    new_rate = config.rate

    # Update the rate (will take effect on next iteration)
    generator_state["rate"] = new_rate

    return {
        "status": "rate_updated",
        "message": f"Rate changed from {old_rate} to {new_rate} events/sec",
        "old_rate": old_rate,
        "new_rate": new_rate
    }


# Keep POST /set-rate for backwards compatibility
@app.post("/set-rate")
async def set_rate(config: GeneratorConfig):
    """Change the event generation rate dynamically (DEPRECATED: use PATCH /rate instead)"""
    return await update_rate(config)


@app.post("/stop")
async def stop_generator():
    """Stop the transaction generator"""
    if not generator_state["running"]:
        return {
            "status": "not_running",
            "message": "Generator is not running"
        }

    generator_state["stop_flag"] = True

    # Wait for thread to stop (max 5 seconds)
    if generator_state["thread"]:
        generator_state["thread"].join(timeout=5)

    return {
        "status": "stopped",
        "message": "Generator stopped successfully"
    }


@app.on_event("startup")
async def startup_event():
    """Auto-start generator on startup at default rate of 5 events/sec"""
    import asyncio
    print("🚀 FastAPI service started")
    print("⏳ Waiting for Redpanda to be ready...")

    # Wait a bit for Redpanda to be ready
    await asyncio.sleep(5)

    print("📊 Auto-starting transaction generator at 5 events/sec...")
    print("💡 Use GET /rate to view current rate, PATCH /rate to change frequency")

    # Auto-start the generator at default rate
    broker = KAFKA_BOOTSTRAP_SERVERS[0] if isinstance(KAFKA_BOOTSTRAP_SERVERS, list) else KAFKA_BOOTSTRAP_SERVERS

    thread = threading.Thread(
        target=run_generator_thread,
        args=(broker,),
        daemon=True
    )
    thread.start()
    generator_state["thread"] = thread
    generator_state["rate"] = EVENTS_PER_SECOND
    print("✅ Generator auto-started at 5 events/sec")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
