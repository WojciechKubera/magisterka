# MSc20WojciechKubera
MSc20WojciechKubera

pipeline.py - Skrypt wykorzystującu plik MLCQCodeSmellSamples.csv, który zawiera odnośniki do repozytorów wykorzystane w orginalnych badaniach. Są one wykorzystene do ich pobrania. Nastepnie do próbek znajdujących sie w pliku .csv ją obliczane są metryki kodu przy uzyciu narzędzia Java code metrics calculator (CK). Efektem końcowym jest powstanie plików class_results i method_results w których zawierają się rekordy z MLCQCodeSmellSamples.csv z odpowiednio dodanymi do każdego rekoru wynikami obliczonych metryk.

Skrypty znajdujące sie w folderach Neural network, Random Forest, oraz Knn wykorzystuja pliki class_results.csv i method_results.csv do konstruowania poszczególnych modeli predykcji brzydkich zapachów kodu. Skrypty generują i zapisują tablice pomyłek zbudowanych modeli.


