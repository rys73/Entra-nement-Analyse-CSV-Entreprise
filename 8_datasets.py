import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

chemin_fichier = r"C:\Users\ighik\OneDrive\Escritorio\html\py-js\fichier_csv\fichiers_8\8_datasets.csv"
chemin_sauvegarde = r"C:\Users\ighik\OneDrive\Escritorio\html\py-js\fichier_csv\fichiers_8\8_datasets_sauvegarde.csv"
chemin_pdf = r"C:\Users\ighik\OneDrive\Escritorio\html\py-js\fichier_csv\fichiers_8\8_graphiques.pdf"

fichier = pd.read_csv(chemin_fichier, parse_dates=["Date_Embauche"], encoding="utf-8-sig")
figures = []

# 1.1 CA TOTAL PAR EMPLOYE
colonne_vente = [f"Ventes_Mois{str(i).zfill(2)}" for i in range (1,13)]
fichier["CA"] = fichier.groupby("ID")[colonne_vente].transform("sum").sum(axis=1)
fichier["Remise"] = fichier["Remise"] / 100
fichier["CA"] = fichier["CA"] - (fichier["Remise"] * fichier["CA"])
# 1.2 SALAIRE TOTAL PAR EMPLOYE
fichier["Salaire_Annuel"] = fichier["Salaire"] * 12
fichier["Salaire_Total"] = fichier["Salaire_Annuel"] + fichier["Prime"] + fichier["Bonus_Annuel"]
# 1.3 RATIO CA SALAIRE
fichier["Ratio_CA_Salaire"] = fichier["CA"] / fichier["Salaire_Total"]

# 2.1 SCORE PONDORE
fichier["Anciennete"] = pd.Timestamp.now().year - fichier["Date_Embauche"].dt.year
fichier["Score_Pondere"] = ((fichier["Performance_Score"] * fichier["Anciennete"])/10)
fichier["Score_Pondere"] = fichier["Score_Pondere"] * fichier["Ratio_CA_Salaire"]
# 2.2 INDICE DE PERFORMANCE NORMALISé
fichier["Indice_Performance_Normalise"] = fichier["Score_Pondere"] / fichier["CA"]
fichier["Indice_Performance_Normalise"] = (
    (fichier["Indice_Performance_Normalise"] - fichier["Indice_Performance_Normalise"].min()) /
    (fichier["Indice_Performance_Normalise"].max() - fichier["Indice_Performance_Normalise"].min()))
# 2.3 HEATMAP : TOP 25 INDICE DE PERFORMANCE NORMALISé
top_indice_performance = fichier.nlargest(25, "Indice_Performance_Normalise")
top_indice_performance["ID_Nom"] = (
    top_indice_performance["ID"].astype(str)
    +"-"+
    top_indice_performance["Nom"])
fig1 = plt.figure(figsize=(12,6))
sns.heatmap(top_indice_performance.set_index("ID_Nom")[["Indice_Performance_Normalise"]],
            annot=True, cmap="YlOrRd")
plt.title("Top 25 Employés par Indice de Performance Normalisé")
figures.append(fig1)
plt.close()

# 3.1 RATIO SUR L'AGE PAR RAPPORT A L'ANCIENNETE
fichier["Ratio_Age_Anciennete"] = fichier["Age"] / fichier["Anciennete"]

# 4.1 CATEGORIE AGE
fichier["Categorie_Age"] = pd.cut(
    fichier["Age"],
bins=[20, 24, 29, 34, 39, 44, 49, 54, 59, 69],
labels=["Jeune employé", "Jeune professionnel",
        "Professionnel confirmé", "Expérimenté", "Senior 1", "Senior 2",
        "Expert", "Pré-retraire", "Retraité / Consultant"])
# 4.2 CA EMPLOYE MOYEN PAR VILLE, DEPARTEMENT, CATEGORIE AGE, PROJET, PRODUIT
CA_moyen_ville = (fichier.groupby("Ville")
                        .agg(CA_Moyen_Ville=("CA","mean"),
                            Nb_Vendeurs=("ID", "count")).reset_index().round(2).sort_values(by="CA_Moyen_Ville", ascending=False))
CA_moyen_departement = (fichier.groupby("Departement")
                        .agg(CA_Moyen_Dep=("CA","mean"),
                            Nb_Vendeurs=("ID", "count")).reset_index().round(2).sort_values(by="CA_Moyen_Dep", ascending=False))
CA_moyen_categorie_age = (fichier.groupby("Categorie_Age", observed=True)
                        .agg(CA_Moyen_Cat_Age=("CA","mean"),
                            Nb_Vendeurs=("ID", "count")).reset_index().round(2).sort_values(by="CA_Moyen_Cat_Age", ascending=False))
CA_moyen_projet = (fichier.groupby("Projet")
                        .agg(CA_Moyen_Projet=("CA","mean"),
                            Nb_Vendeurs=("ID", "count")).reset_index().round(2).sort_values(by="CA_Moyen_Projet", ascending=False))
CA_moyen_produit = (fichier.groupby("Produit")
                        .agg(CA_Moyen_Produit=("CA","mean"),
                            Nb_Vendeurs=("ID", "count")).reset_index().round(2).sort_values(by="CA_Moyen_Produit", ascending=False))

# 5.1 DECTECTER LES CORRELATIONS 
corr1 = fichier["Heures_Semaine"].corr(fichier["Performance_Score"]).round(2)
print("Corrélation Heures par Semaine vs Performance Score :", corr1)
corr2 = fichier["CA"].corr(fichier["Prime"]).round(2)
print("Corrélation CA Total Par Employé vs Prime :", corr2)

# 6.1 CALCUL : MOYENNE ET ECART-TYPE
moyenne_score = fichier["Score_Pondere"].mean()
ecart_type = fichier["Score_Pondere"].std()
# 6.2 PERFORMANCE LEVEL
fichier["Performance_Level"] = pd.cut(
    fichier["Score_Pondere"],
    bins=[-float("inf"), moyenne_score - ecart_type, moyenne_score + ecart_type, float("inf")],
    labels=["Low", "Medium", "High"])
# 6.3 TOP PERFORMANCE = TRUE POUR PEROFMANCE LEVEL : HIGH
fichier["Top_Performers"] = fichier["Performance_Level"] == "High"

# 7.1 CLV (COSTUMER LIFETIME VALUES=)
clv = fichier.groupby("Client_ID")["CA"].sum().reset_index()
clv.rename(columns={"CA": "CLV"}, inplace=True)
# 7.2 AJOUTER LA COLONNE CLV AU FICHIER
fichier = fichier.merge(clv, on="Client_ID", how="left")
# 7.3 HEATMAP TOP 25
top_CLV = fichier.groupby("Client_ID")["CLV"].first().nlargest(25).reset_index()
fig2 = plt.figure(figsize=(12,6))
sns.heatmap(top_CLV.set_index("Client_ID")[["CLV"]],
            annot=True,fmt=".0f" ,cmap="YlOrRd", linewidths=0.5,
            vmin=top_CLV["CLV"].min(),vmax=top_CLV["CLV"].max())
plt.title("Top 25 Clients par CLV")
figures.append(fig2)
plt.close()

# 8.1 CALCUL DE MARGE
marge_produit = fichier.groupby("Produit")["CA"].sum().reset_index()
marge_produit["Marge"] = (marge_produit["CA"] * 0.3).round(2)
marge_produit = marge_produit.sort_values("Marge", ascending=False)

# 9.1 CALCUL CA TOTAL PAR MOIS
ventes_par_mois = fichier[colonne_vente].sum().reset_index()
ventes_par_mois.columns = ["Mois", "CA_Total"]
# 9.2 GRAPHIQUE : EVOLUTION CA PAR MOIS
fig3 = plt.figure(figsize=(12,6))
plt.plot(ventes_par_mois["Mois"], ventes_par_mois["CA_Total"], marker="o", label="CA Mensuel")
plt.title("Evolution du CA Mensuel")
plt.xlabel("Mois")
plt.ylabel("CA TOTAL (€)")
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
figures.append(fig3)
plt.close()

# 10.1 SCORE D'EFFICACITE PAR EMPLOYE SUR 20
fichier["Score_Efficacite_20"] = (fichier["CA"] * fichier["Score_Pondere"]) / fichier["Heures_Semaine"]
fichier["Score_Efficacite_20"] = (
    (fichier["Score_Efficacite_20"] - fichier["Score_Efficacite_20"].min())
    / (fichier["Score_Efficacite_20"].max() - fichier["Score_Efficacite_20"].min()))*20

# 11.1 BOXPLOT + SWARMPLOT POUR PERFORMANCE SCORE
fig4 = plt.figure(figsize=(12,6))
sns.boxplot(
    x="Categorie_Age", y="Performance_Score",
      data=fichier, showfliers=False, color="lightblue", width=0.5)
sns.swarmplot(
    x="Categorie_Age", y="Performance_Score",
    data=fichier, hue="Departement", dodge=True, size=4.4, alpha=0.7)
plt.title("Performance Score par Catégorie d'Age et Département", fontsize=14)
plt.xlabel("Catégorie d'Age")
plt.ylabel("Performance Score")
plt.legend(title="Département", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.xticks(rotation=45)
plt.tight_layout(pad=2.0)
plt.subplots_adjust(bottom=0.21)
figures.append(fig4)
plt.close()

# 12.1 REMISE CATEGORISE ET CALCUL CA TOTAL PAR PRODUIT
fichier["Remise_Categorie"] = fichier["Remise"].apply(lambda x: "Avec Remise" if x > 0 else "Sans Remise")
fichier["CA_Total_Produit"] = fichier.groupby("Produit")["CA"].transform("sum")
# 12.2 PIVOT POUR LES DONNEES EMPILEES
pivot = fichier.pivot_table(
    index="Produit", columns="Remise_Categorie", 
    values="CA_Total_Produit", aggfunc="sum", fill_value=0)
# 12.3 HISTOGRAMME EMPILE COMPACT
ax = pivot.plot(
    kind="bar", stacked=True, width=0.7,
    color=["skyblue", "orange"])
fig5 = plt.figure(figsize=(12,6))
plt.title("Répartition des ventes avec/sans remise par produit")
plt.xlabel("Produit")
plt.ylabel("CA Total")
plt.legend(title="Remise")
plt.tight_layout()
for c in ax.containers:
    ax.bar_label(c, label_type="center", fmt="%.0f")
figures.append(fig5)
plt.close()

# 13.1 EMPLOYE SOUS-PERFORMANT
seuil_sous_performance= moyenne_score - ecart_type
employe_sous_performant = fichier.query("Score_Pondere < @seuil_sous_performance ")
# 14.1 CLV FAIBLE
moyenne_clv = fichier["CLV"].mean()
clients_clv_faible = fichier.query("CLV < @moyenne_clv/2")
# 15.1 ENREGISTRER LE DATASET DANS UN CSV SAUVEGARDE
fichier = fichier.round(2)
fichier.to_csv(chemin_sauvegarde, index=False, encoding="utf-8-sig")
# 15.1 ENREGISTRER TOUTES LES VISUALISATIONS EN PDF
with PdfPages(chemin_pdf) as pdf:
    for fig in figures:
        pdf.savefig(fig)

