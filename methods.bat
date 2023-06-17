@echo off
python generateUniqueProjects.py
mkdir process
move  genMethods.py process
move  run.bat process
move  UniqueProjects.csv process
cd process
call run.bat
python genMethods.py
