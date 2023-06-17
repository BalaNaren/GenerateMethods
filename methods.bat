python generateUniqueProjects.py
mkdir process
move  genMethods.py process
move  run.sh process
move  UniqueProjects.csv process
cd process
run.bat
python genMethods.py
