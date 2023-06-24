python3 generateUniqueProjects.py
mkdir process
cp  genMethods.py process
cp  run.sh process
cp  UniqueProjects.csv process
cp all-polluter-cleaner-info-combined-filtered-fp.csv process
cp processedOrgCsv_P7.csv process
cd process
bash run.sh
python3 genMethods.py
