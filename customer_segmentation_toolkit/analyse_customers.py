# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/04_analyse_customers.ipynb (unless otherwise specified).

__all__ = ['build_transactions_per_user', 'compute_n_customers_with_unique_purchase', 'convert_customers_df_to_np',
           'analyse_customers_pca', 'plot_customers_pca', 'compute_customer_clusters', 'plot_customer_categories',
           'add_customer_clusters_info', 'compute_aggregated_customer_clusters_info']

# Cell
import logging
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

# Cell

def build_transactions_per_user(
    basket_price: pd.DataFrame,
    n_purchase_clusters: int,
) -> pd.DataFrame:

    # nb de visites et stats sur le montant du panier / utilisateurs
    transactions_per_user = basket_price.groupby(by=['CustomerID'])['Basket Price']\
                                        .agg(['count','min','max','mean','sum'])
    for i in range(n_purchase_clusters):
        col = 'categ_{}'.format(i)
        transactions_per_user.loc[:,col] = basket_price.groupby(by=['CustomerID'])\
                                                        [col].sum() / transactions_per_user['sum']*100
    transactions_per_user.reset_index(drop=False, inplace=True)

    last_date = basket_price['InvoiceDate'].max().date()

    first_registration = pd.DataFrame(basket_price.groupby(by=['CustomerID'])['InvoiceDate'].min())
    last_purchase      = pd.DataFrame(basket_price.groupby(by=['CustomerID'])['InvoiceDate'].max())

    test  = first_registration.applymap(lambda x:(last_date - x.date()).days)
    test2 = last_purchase.applymap(lambda x:(last_date - x.date()).days)

    transactions_per_user.loc[:, 'LastPurchase'] = test2.reset_index(drop = False)['InvoiceDate']
    transactions_per_user.loc[:, 'FirstPurchase'] = test.reset_index(drop = False)['InvoiceDate']

    return transactions_per_user

# Cell

def compute_n_customers_with_unique_purchase(transactions_per_user: pd.DataFrame):
    return transactions_per_user[transactions_per_user['count'] == 1].shape[0]

# Cell

def convert_customers_df_to_np(
    transactions_per_user: pd.DataFrame,
    n_purchase_clusters: int,
) -> np.ndarray:
    list_cols = ['count','min','max','mean'] + [f'categ_{i}' for i in range(n_purchase_clusters)]
    matrix = transactions_per_user[list_cols].to_numpy()
    return matrix


def analyse_customers_pca(
    matrix: np.ndarray,
    n_components=None,
) -> pd.DataFrame:
    scaler = StandardScaler()
    scaler.fit(matrix)
    # print('variables mean values: \n' + 90*'-' + '\n' , scaler.mean_)
    scaled_matrix = scaler.transform(matrix)

    pca = PCA()
    pca.fit(scaled_matrix)
    #pca_samples = pca.transform(scaled_matrix)

    return scaled_matrix, pca

# Cell

import matplotlib.pyplot as plt
import seaborn as sns

def plot_customers_pca(matrix: np.ndarray, pca: PCA):
    fig, ax = plt.subplots(figsize=(14, 5))
    sns.set(font_scale=1)
    plt.step(range(matrix.shape[1]), pca.explained_variance_ratio_.cumsum(), where='mid',
             label='cumulative explained variance')
    sns.barplot(np.arange(1,matrix.shape[1]+1), pca.explained_variance_ratio_, alpha=0.5, color = 'g',
                label='individual explained variance')
    plt.xlim(0, 10)

    ax.set_xticklabels([s if int(s.get_text())%2 == 0 else '' for s in ax.get_xticklabels()])

    plt.ylabel('Explained variance', fontsize = 14)
    plt.xlabel('Principal components', fontsize = 14)
    plt.legend(loc='best', fontsize = 13);

# Cell

def compute_customer_clusters(
    scaled_matrix: np.ndarray,
    n_clusters: int,
) -> np.ndarray:
    kmeans = KMeans(init='k-means++', n_clusters=n_clusters, n_init=100)
    kmeans.fit(scaled_matrix)
    clusters = kmeans.predict(scaled_matrix)
    return clusters

# Cell

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns


def plot_customer_categories(
    scaled_matrix: np.ndarray,
    clusters_clients: np.ndarray,
    n_customer_clusters: int,
):
    mat = pd.DataFrame(scaled_matrix)
    mat['cluster'] = pd.Series(clusters_clients)

    sns.set_style("white")
    sns.set_context("notebook", font_scale=1, rc={"lines.linewidth": 2.5})

    LABEL_COLOR_MAP = {0:'r', 1:'tan', 2:'b', 3:'k', 4:'c', 5:'g', 6:'deeppink', 7:'skyblue', 8:'darkcyan', 9:'orange',
                       10:'yellow', 11:'tomato', 12:'seagreen'}
    label_color = [LABEL_COLOR_MAP[l] for l in mat['cluster']]

    fig = plt.figure(figsize = (12,10))
    increment = 0
    for ix in range(6):
        for iy in range(ix+1, 6):
            increment += 1
            ax = fig.add_subplot(4,3,increment)
            ax.scatter(mat[ix], mat[iy], c= label_color, alpha=0.5)
            plt.ylabel('PCA {}'.format(iy+1), fontsize = 12)
            plt.xlabel('PCA {}'.format(ix+1), fontsize = 12)
            ax.yaxis.grid(color='lightgray', linestyle=':')
            ax.xaxis.grid(color='lightgray', linestyle=':')
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            if increment == 12: break
        if increment == 12: break

    #_______________________________________________
    # I set the legend: abreviation -> airline name
    comp_handler = []
    for i in range(n_customer_clusters):
        comp_handler.append(mpatches.Patch(color = LABEL_COLOR_MAP[i], label = i))

    plt.legend(handles=comp_handler, bbox_to_anchor=(1.1, 0.9),
               title='Cluster', facecolor = 'lightgrey',
               shadow = True, frameon = True, framealpha = 1,
               fontsize = 13, bbox_transform = plt.gcf().transFigure)

    plt.tight_layout()


# Cell

def add_customer_clusters_info(
    transactions_per_user: pd.DataFrame,
    clusters_clients: np.ndarray,
):
    selected_customers = transactions_per_user.copy(deep = True)
    selected_customers.loc[:, 'cluster'] = clusters_clients

    return selected_customers

# Cell

def compute_aggregated_customer_clusters_info(
    selected_customers: pd.DataFrame,
    n_purchase_clusters: int,
    n_customer_clusters: int,
    categ_threshold: int = 35,
):
    merged_df = pd.DataFrame()
    for i in range(n_customer_clusters):
        test = pd.DataFrame(selected_customers[selected_customers['cluster'] == i].mean())
        test = test.T.set_index('cluster', drop = True)
        test['size'] = selected_customers[selected_customers['cluster'] == i].shape[0]
        merged_df = pd.concat([merged_df, test])

    merged_df.drop('CustomerID', axis = 1, inplace = True)

    merged_df = merged_df.sort_values('sum')

    liste_index = []
    for i in range(n_purchase_clusters):
        column = 'categ_{}'.format(i)
        # XXX: Here we changed the constant: 45 -> categ_threshold
        # Otherwise we get: IndexError: index 0 is out of bounds for axis 0 with size 0
        liste_index.append(merged_df[merged_df[column] > categ_threshold].index.values[0])
    liste_index_reordered = liste_index
    set_index = set(liste_index)
    liste_index_reordered += [ s for s in merged_df.index if s not in set_index]
    merged_df = merged_df.reindex(index = liste_index_reordered)
    merged_df = merged_df.reset_index(drop = False)

    return merged_df

# Cell

# TODO: plot radarchart
# Artem Y: I'm getting a weird error:
#   ValueError: The number of FixedLocator locations (6), usually from a call to set_ticks, does not match the number of ticklabels (5).