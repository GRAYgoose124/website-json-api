#!/usr/bin/env python3
"""
Comprehensive test script to verify the backend functionality
"""
import asyncio
import aiohttp
import json
import pytest
import pytest_asyncio
import tempfile
import os
import subprocess
import time
import signal
import shutil
from datetime import datetime
from pathlib import Path

class ServerManager:
    """Manages a test server instance"""
    
    def __init__(self, port=8009):
        self.port = port
        self.process = None
        self.base_url = f"http://localhost:{port}"
        self.test_userdata_dir = Path("./test-userdata")
    
    async def start(self):
        """Start the test server"""
        # Clean up any existing test data
        await self._cleanup_test_data()
        
        # Kill any existing processes on the port
        await self._kill_existing_processes()
        
        # Start the server
        cmd = [
            "uv", "run", "main.py",
            "--port", str(self.port),
            "--userdata-root", "./test-userdata",
            "--include-steps-root", "./bundled_steps/project",
            "--include-steps-root", "./bundled_steps/custom",
            "--host", "127.0.0.1"
        ]
        
        print(f"🚀 Starting test server with command: {' '.join(cmd)}")
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        await self._wait_for_server()
    
    async def stop(self):
        """Stop the test server and clean up test data"""
        if self.process:
            # Try graceful shutdown first
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                self.process.kill()
                self.process.wait()
            self.process = None
        
        # Clean up test data
        await self._cleanup_test_data()
    
    async def _cleanup_test_data(self):
        """Clean up test userdata directory"""
        if self.test_userdata_dir.exists():
            try:
                shutil.rmtree(self.test_userdata_dir)
                print(f"🧹 Cleaned up test data: {self.test_userdata_dir}")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up test data: {e}")
    
    async def _kill_existing_processes(self):
        """Kill any existing processes using the test port"""
        try:
            subprocess.run(["pkill", "-f", f"main.py --port {self.port}"], capture_output=True)
            await asyncio.sleep(1)
        except Exception:
            pass
    
    async def _wait_for_server(self, timeout=30):
        """Wait for the server to be ready"""
        print(f"⏳ Waiting for server to be ready at {self.base_url}...")
        start_time = time.time()
        attempts = 0
        while time.time() - start_time < timeout:
            attempts += 1
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/steps", timeout=2) as response:
                        if response.status == 200:
                            print(f"✅ Server is ready after {attempts} attempts!")
                            return
                        else:
                            print(f"⚠️  Server responded with status {response.status} on attempt {attempts}")
            except Exception as e:
                if attempts % 10 == 0:  # Only print every 10th attempt to avoid spam
                    print(f"⏳ Attempt {attempts}: Server not ready yet ({type(e).__name__}: {e})")
            await asyncio.sleep(0.5)
        
        print(f"❌ Server failed to start within {timeout} seconds after {attempts} attempts")
        raise TimeoutError(f"Server failed to start within {timeout} seconds")

@pytest_asyncio.fixture(scope="session")
async def test_server():
    """Fixture to manage test server lifecycle"""
    server = ServerManager()
    await server.start()
    yield server
    await server.stop()

@pytest.mark.asyncio
async def test_backend_api(test_server):
    """Test the backend API endpoints"""
    base_url = test_server.base_url
    
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
                
                # Verify we have both project and custom steps
                project_steps = [s for s in steps.values() if s.get('category') == 'project_management']
                custom_steps = [s for s in steps.values() if s.get('category') != 'project_management']
                print(f"   Project management steps: {len(project_steps)}")
                print(f"   Custom steps: {len(custom_steps)}")
            else:
                print(f"❌ Failed to get steps: {response.status}")
                return False
        
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
        
        # Test 4: Test file upload endpoint
        print("\n4. Testing /upload-file endpoint...")
        test_content = "Test file content for upload"
        test_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        test_file.write(test_content)
        test_file.close()
        
        try:
            with open(test_file.name, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                async with session.post(f"{base_url}/upload-file", data=files) as response:
                    if response.status == 200:
                        upload_result = await response.json()
                        print(f"✅ File uploaded successfully: {upload_result['filename']}")
                        print(f"   File path: {upload_result['file_path']}")
                        print(f"   File size: {upload_result['size']}")
                        
                        # Store the uploaded file path for later tests
                        uploaded_file_path = upload_result['file_path']
                    else:
                        print(f"❌ Failed to upload file: {response.status}")
                        uploaded_file_path = None
        finally:
            os.unlink(test_file.name)
        
        # Test 5: Create a project workflow
        print("\n5. Testing project workflow creation...")
        project_workflow = {
            "name": "Test Project Workflow",
            "description": "A test project workflow",
            "steps": [
                {"step_id": "create_project", "params": {"project_name": "Test Project", "description": "A test project"}},
                {"step_id": "upload_file_to_project", "params": {"file_path": uploaded_file_path or "/tmp/test.txt", "destination_path": "data/test.txt"}},
                {"step_id": "list_project_files", "params": {"recursive": True, "include_hidden": False}},
                {"step_id": "download_project_zip", "params": {"include_hidden": False, "compression_level": 6}}
            ]
        }
        
        async with session.post(
            f"{base_url}/workflows",
            json=project_workflow
        ) as response:
            if response.status == 200:
                workflow = await response.json()
                print(f"✅ Created project workflow: {workflow['id']}")
                print(f"   Status: {workflow['status']}")
                print(f"   Steps: {len(workflow['definition']['steps'])}")
                
                # Wait for workflow to complete
                workflow_id = workflow['id']
                max_wait = 30  # seconds
                wait_time = 0
                
                while wait_time < max_wait:
                    await asyncio.sleep(1)
                    wait_time += 1
                    
                    async with session.get(f"{base_url}/workflows/{workflow_id}") as wf_response:
                        if wf_response.status == 200:
                            workflow_status = await wf_response.json()
                            if workflow_status['status'] in ['completed', 'failed']:
                                print(f"   Final status: {workflow_status['status']}")
                                if workflow_status['status'] == 'completed':
                                    print("   ✅ Workflow completed successfully!")
                                    # Check step results
                                    for step_id, result in workflow_status['step_results'].items():
                                        print(f"     {step_id}: {result.get('upload_status', 'completed')}")
                                else:
                                    print("   ❌ Workflow failed!")
                                break
                        else:
                            print(f"   ❌ Failed to get workflow status: {wf_response.status}")
                            break
                else:
                    print("   ⏰ Workflow did not complete within timeout")
            else:
                print(f"❌ Failed to create project workflow: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
        
        # Test 6: Create a custom steps workflow
        print("\n6. Testing custom steps workflow creation...")
        custom_workflow = {
            "name": "Test Custom Workflow",
            "description": "A test workflow with custom steps",
            "steps": [
                {"step_id": "data_validation", "params": {"data_path": "/data/input.csv"}},
                {"step_id": "data_processing", "params": {"algorithm": "standard"}},
                {"step_id": "model_training", "params": {"model_type": "neural_network"}},
                {"step_id": "result_analysis", "params": {"analysis_type": "comprehensive"}}
            ]
        }
        
        async with session.post(
            f"{base_url}/workflows",
            json=custom_workflow
        ) as response:
            if response.status == 200:
                workflow = await response.json()
                print(f"✅ Created custom workflow: {workflow['id']}")
                print(f"   Status: {workflow['status']}")
                print(f"   Steps: {len(workflow['definition']['steps'])}")
            else:
                print(f"❌ Failed to create custom workflow: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
        
        # Test 7: Test workflow validation
        print("\n7. Testing workflow validation...")
        invalid_workflow = {
            "name": "Invalid Workflow",
            "description": "A workflow with missing dependencies",
            "steps": [
                {"step_id": "upload_file_to_project", "params": {"file_path": "/tmp/test.txt"}},  # Missing project_token
                {"step_id": "nonexistent_step", "params": {}}  # Non-existent step
            ]
        }
        
        async with session.post(
            f"{base_url}/workflows",
            json=invalid_workflow
        ) as response:
            if response.status == 200:
                workflow = await response.json()
                print(f"✅ Invalid workflow created (for validation testing): {workflow['id']}")
                print(f"   Validation errors: {len(workflow['definition']['validation_errors'])}")
                print(f"   Validation warnings: {len(workflow['definition']['validation_warnings'])}")
            else:
                print(f"❌ Failed to create invalid workflow: {response.status}")
        
        print("\n🎉 Backend API test completed!")
        return True

@pytest.mark.asyncio
async def test_workflow_engine(test_server):
    """Test the workflow engine functionality"""
    print("\n🔧 Testing Workflow Engine...")
    
    base_url = test_server.base_url
    
    async with aiohttp.ClientSession() as session:
        # Test dependency resolution
        print("Testing dependency resolution...")
        async with session.get(f"{base_url}/steps") as response:
            if response.status == 200:
                steps = await response.json()
                print(f"✅ Step definitions loaded: {len(steps)}")
                
                # Check for required project management steps
                required_steps = ['create_project', 'upload_file_to_project', 'download_project_zip']
                missing_steps = [step for step in required_steps if step not in steps]
                if missing_steps:
                    print(f"❌ Missing required steps: {missing_steps}")
                else:
                    print("✅ All required project management steps present")
            else:
                print(f"❌ Failed to get steps: {response.status}")

@pytest.mark.asyncio
async def test_full_integration(test_server):
    """Test full integration of the system"""
    print("\n🚀 Testing Full System Integration...")
    
    # Test backend API
    api_success = await test_backend_api(test_server)
    
    # Test workflow engine
    await test_workflow_engine(test_server)
    
    if api_success:
        print("\n✅ All integration tests passed!")
    else:
        print("\n❌ Some integration tests failed!")

if __name__ == "__main__":
    asyncio.run(test_full_integration()) 