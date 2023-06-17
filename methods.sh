python generateUniqueProjects.py
mkdir process
mv genMethods.py process
mv run.sh process
mv UniqueProjects.csv process
cd process
bash run.sh
python genMethods.py
