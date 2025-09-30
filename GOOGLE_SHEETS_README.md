# Netflix Subscription Manager avec Google Sheets

Cette version du bot Netflix Subscription Manager utilise Google Sheets comme base de données au lieu de SQLite.

## Comment ça fonctionne

Le bot `botnetflix.py` a les mêmes fonctionnalités que le bot original `bot.py`, mais il stocke toutes les données client dans une feuille de calcul Google au lieu d'une base de données SQLite locale. Cela vous permet de :

1. Accéder à vos données client de n'importe où avec une connexion Internet
2. Partager les données avec les membres de votre équipe
3. Modifier les données directement dans Google Sheets si nécessaire
4. Visualiser et analyser vos données avec les outils de Google Sheets

## Instructions de configuration

### Prérequis

1. Assurez-vous d'avoir installé les packages Python requis :
   ```
   pip install gspread oauth2client
   ```

2. Assurez-vous que votre fichier de compte de service Google est dans le répertoire du projet :
   - Le fichier doit être nommé `bot-netflix-473417-473511-10bd9ccf6f87.json`
   - Si vous avez un fichier de compte de service différent, mettez à jour la variable `SERVICE_ACCOUNT_FILE` dans `googlesheet.py`

3. **Important** : Activez les API Google nécessaires dans votre console Google Cloud :
   - Allez sur [Google Cloud Console](https://console.cloud.google.com/apis/library)
   - Recherchez et activez les API suivantes :
     - Google Sheets API
     - Google Drive API

4. **Configuration de la feuille de calcul** :
   - Allez sur [Google Sheets](https://docs.google.com/spreadsheets)
   - Créez une nouvelle feuille de calcul
   - Renommez-la en "Netflix Clients DB" (ou le nom de votre choix)
   - Partagez-la avec l'adresse email du compte de service en lui donnant les droits d'édition :
     ```
     db-netflix@bot-netflix-473417-473511.iam.gserviceaccount.com
     ```
   - Copiez l'ID de la feuille de calcul depuis l'URL :
     ```
     https://docs.google.com/spreadsheets/d/VOTRE_ID_DE_SPREADSHEET/edit
     ```
   - Ouvrez le fichier `googlesheet.py` et mettez à jour la variable `SPREADSHEET_ID` :
     ```python
     SPREADSHEET_ID = "1a5Pls1g1D_dJ4LGH1uAepUyfZBrZ3yNEtcXs_GCfDsg"  # Remplacez par votre ID
     ```

### Exécution du bot

Pour exécuter la version Google Sheets du bot :
```
python botnetflix.py
```

Lorsque vous l'exécutez, le bot va :
1. S'authentifier auprès de Google Sheets en utilisant le compte de service
2. Se connecter à votre feuille de calcul existante en utilisant l'ID spécifié
3. Vérifier si les onglets "clients" et "burned_tokens" existent, sinon les créer
4. Vérifier si les en-têtes sont présents dans chaque onglet, sinon les ajouter
5. Démarrer le bot Telegram avec toutes les commandes

### Utilisation des commandes

Toutes les commandes du bot fonctionnent exactement comme dans la version SQLite, mais les données sont maintenant stockées dans Google Sheets. Par exemple :

- Quand vous utilisez `/new` pour ajouter un client, une nouvelle ligne est ajoutée à l'onglet "clients"
- Quand vous utilisez `/burn` pour marquer un token comme brûlé, une nouvelle ligne est ajoutée à l'onglet "burned_tokens"

Vous pouvez voir ces modifications en temps réel dans votre feuille de calcul Google Sheets.

## Structure de la feuille de calcul

La feuille de calcul Google aura deux onglets :

1. **clients** - Contient toutes les informations des clients avec les colonnes :
   - id, token, name, email, profile, start_date, end_date, status, payment_amount, is_burned, burn_reason, burn_date

2. **burned_tokens** - Contient des informations sur les tokens brûlés avec les colonnes :
   - id, token, burn_reason, burn_date, client_id

## Commandes

Toutes les commandes du bot original sont prises en charge :

- `/new` - Enregistrer un nouveau client
- `/token` - Voir les détails d'un client
- `/pay` - Marquer un abonnement comme payé
- `/extend` - Prolonger un abonnement
- `/unpaid` - Lister tous les clients non payés
- `/stats` - Voir les statistiques d'abonnement
- `/expiring` - Lister les clients dont l'abonnement expire bientôt
- `/search` - Rechercher des clients
- `/export` - Exporter les données des clients
- `/burn` - Marquer un token comme brûlé
- `/burned` - Lister tous les tokens brûlés
- `/help` - Afficher l'aide
- `/admin` - Vérifier le statut d'administrateur

## Dépannage

### Problèmes d'authentification

Si vous voyez des erreurs comme "Authentication failed" ou "Service account not authorized" :

1. Vérifiez que le fichier `bot-netflix-473417-473511-10bd9ccf6f87.json` est présent dans le répertoire du projet
2. Assurez-vous que les API Google Sheets et Google Drive sont activées dans votre console Google Cloud
3. Vérifiez que vous avez bien partagé votre feuille de calcul avec l'adresse email du compte de service :
   ```
   db-netflix@bot-netflix-473417-473511.iam.gserviceaccount.com
   ```

### Erreur "Spreadsheet not found"

1. Vérifiez que l'ID de spreadsheet dans `googlesheet.py` correspond bien à l'ID de votre feuille de calcul
2. Assurez-vous que la feuille de calcul existe et qu'elle est accessible par le compte de service

### Erreur "The user's Drive storage quota has been exceeded"

Cette erreur se produit lorsque le compte de service n'a plus d'espace de stockage disponible :

1. Utilisez une feuille de calcul existante au lieu d'en créer une nouvelle (comme nous l'avons fait)
2. Mettez à jour la variable `SPREADSHEET_ID` dans `googlesheet.py` avec l'ID de votre feuille de calcul

### Problèmes avec les onglets ou les en-têtes

Si les onglets "clients" ou "burned_tokens" sont vides ou n'ont pas les bons en-têtes :

1. Le bot vérifie maintenant automatiquement les en-têtes et les ajoute si nécessaire
2. Si vous rencontrez encore des problèmes, vous pouvez supprimer les onglets existants et laisser le bot les recréer

## Comparaison avec le bot original

Fonctionnalité | Bot original (bot.py) | Bot Google Sheets (botnetflix.py)
--------------|----------------------|-----------------------------
Stockage | Base de données SQLite locale | Feuille de calcul Google
Accès | Local uniquement | Partout avec une connexion Internet
Partage | Pas facilement partageable | Peut être partagé avec les membres de l'équipe
Édition | Uniquement via les commandes du bot | Commandes du bot ou édition directe de la feuille de calcul
Visualisation | Commandes limitées | Toutes les fonctionnalités de Google Sheets (graphiques, filtres, etc.)
Exportation | Fichiers CSV/Excel | Fichiers CSV/Excel + intégration avec d'autres services Google
Commandes | Toutes les commandes standard | Toutes les commandes standard
Sécurité | Locale uniquement | Authentification Google et contrôle d'accès

## Avantages de l'utilisation de Google Sheets

### 1. Visualisation et analyse des données

Avec Google Sheets, vous pouvez facilement :
- Créer des graphiques pour visualiser les tendances d'abonnement
- Utiliser des filtres pour analyser des segments spécifiques de clients
- Appliquer des formules pour calculer des statistiques personnalisées

### 2. Collaboration en temps réel

- Plusieurs personnes peuvent consulter et modifier les données simultanément
- Commentaires et suggestions directement dans la feuille de calcul
- Historique des modifications pour suivre qui a fait quoi et quand

### 3. Intégration avec d'autres services

- Connectez vos données à Google Data Studio pour des tableaux de bord avancés
- Intégration avec Google Apps Script pour des automatisations personnalisées
- Exportation facile vers d'autres formats et services

## Conclusion

Le bot Netflix Subscription Manager avec Google Sheets combine la puissance du bot Telegram original avec la flexibilité et l'accessibilité de Google Sheets. Cette solution est idéale pour les utilisateurs qui souhaitent accéder à leurs données de n'importe où, collaborer avec une équipe, ou profiter des fonctionnalités avancées d'analyse et de visualisation de Google Sheets.
