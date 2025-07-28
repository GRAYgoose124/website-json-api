#!/usr/bin/env python3
"""
Simple test script to verify the backend functionality
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_backend():
    """Test the backend API endpoints"""
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Backend API...")
        
        # Test 1: Get available steps
        print("\n1. Testing /steps endpoint...")
        async with session.get(f"{base_url}/steps") as response:
            if response.status == 200:
                steps = await response.json()
                print(f"✅ Found {len(steps)} available steps:")
                for step_id, step in steps.items():
                    print(f"   - {step['name']}: {step['description']}")
            else:
                print(f"❌ Failed to get steps: {response.status}")
        
        # Test 2: Get notices
        print("\n2. Testing /notices endpoint...")
        async with session.get(f"{base_url}/notices") as response:
            if response.status == 200:
                notices = await response.json()
                print(f"✅ Found {len(notices)} notices")
            else:
                print(f"❌ Failed to get notices: {response.status}")
        
        # Test 3: Get workflows
        print("\n3. Testing /workflows endpoint...")
        async with session.get(f"{base_url}/workflows") as response:
            if response.status == 200:
                workflows = await response.json()
                print(f"✅ Found {len(workflows)} workflows")
            else:
                print(f"❌ Failed to get workflows: {response.status}")
        
        # Test 4: Create a test workflow
        print("\n4. Testing workflow creation...")
        test_workflow = {
            "name": "Test Workflow",
            "description": "A test workflow for validation",
            "steps": [
                {"step_id": "data_validation", "params": {"data_path": "/test/data.csv"}},
                {"step_id": "data_processing", "params": {"algorithm": "standard"}}
            ]
        }
        
        async with session.post(
            f"{base_url}/workflows",
            json=test_workflow
        ) as response:
            if response.status == 200:
                workflow = await response.json()
                print(f"✅ Created workflow: {workflow['id']}")
                print(f"   Status: {workflow['status']}")
                print(f"   Steps: {len(workflow['definition']['steps'])}")
            else:
                print(f"❌ Failed to create workflow: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
        
        print("\n🎉 Backend test completed!")

if __name__ == "__main__":
    asyncio.run(test_backend()) 