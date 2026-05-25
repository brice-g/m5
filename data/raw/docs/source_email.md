- **Qui** produit cette donnée ? (clients via leur boîte mail)
- **Quelle volumétrie** réelle estimer ? (à partir du fichier fourni, extrapoler à un mois, un an)
- **Quel format brut** (`mbox`) et quels champs portent une info exploitable (`From`, `Subject`, `Date`, `Body`, `Message-ID`, `In-Reply-To`)
- **Quelles données personnelles** sont nécessairement présentes (adresse email, nom dans la signature, références client) → rappel des règles M2 sur l'anonymisation
- **Quels biais ce canal va-t-il introduire** dans le dataset global ? (clientèle email = profil plus âgé, demandes plus longues et plus formelles que le chat — à vérifier au Brief 2)

## 1. Qui produit cette donnée ?

La donnée est produite par les clients de l'entreprise FastIA. Ils utilisent leur messagerie personnelle ou professionnelle pour contacter le support technique, commercial ou facturation.

## 2. Quelle volumétrie réelle estimer ?
Pour extrapoler, nous devons d'abord analyser l'échantillon fourni :
* Données actuelles : 8 emails reçus sur une période de 5 jours (du 6 au 10 avril 2026).  
* Moyenne : Environ 1,6 email par jour ouvré.Extrapolation à un mois (20 jours ouvrés) : Environ 32 emails / mois.
* Extrapolation à un an : Environ 380 à 400 emails / an.

*Note :* Cette estimation est une base minimale. En réalité, le volume peut fluctuer selon les pannes (comme l'erreur de session en boucle ) ou les périodes de facturation.


## 3. Format brut et champs exploitables

Le format est le .mbox, un format standard de stockage d'emails qui concatène les messages les uns après les autres dans un seul fichier texte.

| Champ | Utilité pour l'exploitation |
| :--- | :--- |
| **From** | Identifier l'expéditeur et son domaine (ex: @studio-roussel.fr). |
| **Subject** | "Classifier automatiquement l'intention (Facturation, Technique, Devis)." |
| **Date** | Analyser les pics d'activité ou les délais de réponse du support.|
| **Body** (Corps) | Extraire le problème précis grâce au traitement du langage naturel (NLP). |
| **Message-ID** | Identifiant unique pour le suivi technique et l'indexation. |
| **In-Reply-To** | Essentiel pour lier les messages et reconstituer une conversation (fil de discussion). |


## 4. Données personnelles présentes (RGPD)
Le fichier contient de nombreuses Données à Caractère Personnel (DCP) qu'il convient d'anonymiser selon les règles du M2 :
* **Identité :** Noms et prénoms (ex: Camille Roussel, Thomas Legendre).  
* **Coordonnées :** Adresses emails directes et numéros de téléphone.  
* **Données professionnelles :** Noms d'entreprises et fonctions (DSI, RSSI).  
* **Identifiants clients :** Références internes (PRO-44219, ENT-9921). 
* **Données financières :** Numéros de factures et montants payés.

## 5. Biais introduits par le canal Email
Utiliser uniquement l'email pour constituer un dataset introduit plusieurs biais :
* **Profil sociologique :** L'email est souvent privilégié par une clientèle plus âgée ou des profils B2B (cadres, administratifs). Les profils plus jeunes ou "grand public" utilisent souvent le chat ou les réseaux sociaux.  
* **Forme et ton :** Les demandes sont plus longues, structurées et formelles ("Cordialement", signatures complètes). Un modèle d'IA entraîné uniquement là-dessus pourrait ne pas comprendre le langage court et direct d'un chat.  
* **Biais de sélection (Sévérité) :** L'email est souvent utilisé pour des problèmes complexes (migration d'instance, demande de devis) ou graves (réclamation juridique, phishing). Les questions simples de type "comment faire X" sont souvent déjà filtrées par la FAQ ou le chat.  
* **Délai de réponse :** L'email est un canal asynchrone ; les clients acceptent d'attendre 24/48h, contrairement au chat qui exige de l'instantanéité.