✅ COMPLETED:
- ✅ backend project_paths are now relative to the userdata_root / projects folder (not absolute, to avoid exposing fs to api)
- ✅ uploads now only happen after workflow is submitted and not during ui interaction
- ✅ can copy workflows we create in the ui to paste and rerun them

REMAINING:
- projects/.index.dat (if needed)
- Additional frontend API tests for comprehensive coverage
- Performance optimization for large file uploads
- Enhanced error handling and user feedback