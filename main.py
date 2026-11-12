import sys

from PySide6.QtCore import Qt, QDate, QEvent
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QInputDialog,
    QDateEdit,
    QComboBox,
    QFormLayout,
    QCalendarWidget,
    QGroupBox,
    QSpinBox,
    QGridLayout,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCompleter,
    QLineEdit,
)

from database import create_database, get_connection


# ============================================================
# BIBLIOTHÈQUE
# ============================================================

class BibliothequeWidget(QWidget):

    CATEGORIES = {
        "Potages": "POTAGE",
        "Plats": "PLAT",
        "Desserts": "DESSERT",
    }

    def __init__(self):
        super().__init__()

        self.categorie = "POTAGE"

        self.creer_interface()
        self.charger_elements()

    def creer_interface(self):

        layout_principal = QVBoxLayout(self)

        self.titre = QLabel("Bibliothèque - Potages")
        self.titre.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout_principal.addWidget(self.titre)

        self.tabs = QTabWidget()

        for nom, categorie in self.CATEGORIES.items():

            page = QWidget()
            page_layout = QVBoxLayout(page)

            recherche = QLineEdit()
            recherche.setPlaceholderText("Rechercher...")

            recherche.textChanged.connect(lambda texte, cat=categorie:self.filtrer(texte, cat))

            page_layout.addWidget(recherche)

            liste = QListWidget()

            liste.itemDoubleClicked.connect(lambda item, cat=categorie:self.modifier_element(cat))

            page_layout.addWidget(liste)

            boutons = QHBoxLayout()

            bouton_ajouter = QPushButton("Ajouter")
            bouton_modifier = QPushButton("Modifier")
            bouton_desactiver = QPushButton("Désactiver")

            bouton_ajouter.clicked.connect(lambda checked=False, cat=categorie:self.ajouter_element(cat)
            )

            bouton_modifier.clicked.connect(lambda checked=False, cat=categorie:self.modifier_element(cat))

            bouton_desactiver.clicked.connect(lambda checked=False, cat=categorie:self.desactiver_element(cat))

            boutons.addWidget(bouton_ajouter)
            boutons.addWidget(bouton_modifier)
            boutons.addWidget(bouton_desactiver)

            page_layout.addLayout(boutons)

            self.tabs.addTab(page, nom)

        self.tabs.currentChanged.connect(self.changer_categorie)

        layout_principal.addWidget(self.tabs)

    def changer_categorie(self, index):

        nom_onglet = self.tabs.tabText(index)

        self.categorie = self.CATEGORIES[nom_onglet]

        self.titre.setText(f"Bibliothèque - {nom_onglet}")

        self.charger_elements()

    def charger_elements(self):

        index = self.tabs.currentIndex()

        if index < 0:
            return

        nom_onglet = self.tabs.tabText(index)

        categorie = self.CATEGORIES[nom_onglet]

        page = self.tabs.widget(index)

        liste = page.findChild(QListWidget)

        if liste is None:
            return

        liste.clear()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, nom
            FROM bibliotheque
            WHERE categorie = ?
            AND actif = 1
            ORDER BY nom COLLATE NOCASE
            """,
            (categorie,),
        )

        elements = cursor.fetchall()

        conn.close()

        for element_id, nom in elements:

            item = QListWidgetItem(nom)

            item.setData(Qt.ItemDataRole.UserRole, element_id)

            liste.addItem(item)

    def filtrer(self, texte, categorie):

        index = self.tabs.currentIndex()

        nom_onglet = self.tabs.tabText(index)

        if self.CATEGORIES[nom_onglet] != categorie:
            return

        page = self.tabs.widget(index)

        liste = page.findChild(QListWidget)

        for i in range(liste.count()):

            item = liste.item(i)

            visible = texte.lower() in item.text().lower()

            item.setHidden(not visible)

    def ajouter_element(self, categorie):

        texte, ok = QInputDialog.getText(self, "Ajouter", "Nom :")

        if not ok:
            return

        texte = texte.strip()

        if not texte:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM bibliotheque
            WHERE categorie = ?
            AND nom = ?
            """,
            (categorie, texte),
        )

        if cursor.fetchone():
            conn.close()
            QMessageBox.warning(self, "Doublon", "Cet élément existe déjà.")
            return

        cursor.execute(
            """
            INSERT INTO bibliotheque
            (categorie, nom, actif)
            VALUES (?, ?, 1)
            """,
            (categorie, texte),
        )

        conn.commit()
        conn.close()

        self.charger_elements()

    def modifier_element(self, categorie):

        item = self.element_selectionne()

        if item is None:
            QMessageBox.information(self, "Modification", "Sélectionne un élément.")
            return

        element_id = item.data(Qt.ItemDataRole.UserRole)

        ancien_nom = item.text()

        nouveau_nom, ok = QInputDialog.getText(self, "Modifier", "Nom :", text=ancien_nom)

        if not ok:
            return

        nouveau_nom = nouveau_nom.strip()

        if not nouveau_nom:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE bibliotheque
            SET nom = ?
            WHERE id = ?
            """,
            (nouveau_nom, element_id),
        )

        conn.commit()
        conn.close()

        self.charger_elements()

    def desactiver_element(self, categorie):

        item = self.element_selectionne()

        if item is None:
            QMessageBox.information(self, "Désactivation", "Sélectionne un élément.")
            return

        element_id = item.data(Qt.ItemDataRole.UserRole)

        nom = item.text()

        confirmation = QMessageBox.question(self, "Désactiver", f"Voulez-vous désactiver « {nom} » ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE bibliotheque
            SET actif = 0
            WHERE id = ?
            """,
            (element_id,),
        )

        conn.commit()
        conn.close()

        self.charger_elements()

    def element_selectionne(self):

        index = self.tabs.currentIndex()

        page = self.tabs.widget(index)

        liste = page.findChild(QListWidget)

        if liste is None:
            return None

        return liste.currentItem()


# ============================================================
# CALENDRIER
# ============================================================

class CalendrierSansMolette(QCalendarWidget):

    def __init__(self):
        super().__init__()

        # Intercepter la molette sur le calendrier
        self.installer_filtre_molette()

    def installer_filtre_molette(self):

        # Le calendrier lui-même
        self.installEventFilter(self)

        # Et tous ses widgets internes
        for widget in self.findChildren(QWidget):
            widget.installEventFilter(self)

    def eventFilter(self, watched, event):

        if event.type() == QEvent.Type.Wheel:

            scroll_area = self.parentWidget()

            while scroll_area is not None:

                if isinstance(scroll_area, QScrollArea):

                    delta = event.angleDelta().y()

                    barre = scroll_area.verticalScrollBar()

                    # Défilement de la page
                    barre.setValue(barre.value() - delta)

                    event.accept()

                    return True

                scroll_area = scroll_area.parentWidget()

        return super().eventFilter(watched, event)

class CalendrierWidget(QWidget):

    TYPES = {
        "Jour férié": "FERIE",
        "Congé scolaire": "CONGE",
        "Fermeture exceptionnelle": "FERMETURE",
    }

    COULEURS = {
        "FERIE": "#cc5f2c",
        "CONGE": "#fabb00",
        "FERMETURE": "#1a7eca",
    }

    def __init__(self):
        super().__init__()

        self.creer_interface()
        self.charger_fermetures()
        self.actualiser_calendrier()

    # ==========================================================
    # INTERFACE
    # ==========================================================

    def creer_interface(self):

        layout_principal = QVBoxLayout(self)

        # ------------------------------------------------------
        # Titre
        # ------------------------------------------------------

        titre = QLabel("Calendrier")

        titre.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout_principal.addWidget(titre)

        # ------------------------------------------------------
        # Année
        # ------------------------------------------------------

        barre_annee = QHBoxLayout()

        label_annee = QLabel("Année :")

        self.annee = QSpinBox()
        self.annee.setRange(2000, 2100)
        self.annee.setValue(QDate.currentDate().year())

        self.annee.valueChanged.connect(self.actualiser_calendrier)

        barre_annee.addWidget(label_annee)
        barre_annee.addWidget(self.annee)
        barre_annee.addStretch()

        layout_principal.addLayout(barre_annee)

        # ------------------------------------------------------
        # Zone défilante
        # ------------------------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        contenu = QWidget()

        contenu_layout = QVBoxLayout(contenu)

        # ------------------------------------------------------
        # Légende
        # ------------------------------------------------------

        legende = QHBoxLayout()

        legende.addWidget(self.creer_legende("Jour férié", "#cc5f2c"))

        legende.addWidget(self.creer_legende("Congé scolaire", "#fabb00"))

        legende.addWidget(self.creer_legende("Fermeture exceptionnelle", "#1a7eca"))

        legende.addStretch()

        contenu_layout.addLayout(legende)

        # ------------------------------------------------------
        # Les 12 mois
        # ------------------------------------------------------

        grille = QGridLayout()

        self.calendriers = []

        for mois in range(1, 13):

            calendrier = CalendrierSansMolette()

            calendrier.setGridVisible(True)

            calendrier.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

            calendrier.setNavigationBarVisible(False)

            calendrier.setMinimumHeight(240)

            self.calendriers.append(calendrier)

            groupe = QGroupBox(self.nom_mois(mois))

            groupe_layout = QVBoxLayout(groupe)

            groupe_layout.addWidget(calendrier)

            ligne = (mois - 1) // 3
            colonne = (mois - 1) % 3

            grille.addWidget(groupe, ligne, colonne)

        contenu_layout.addLayout(grille)

        # ------------------------------------------------------
        # Séparateur
        # ------------------------------------------------------

        contenu_layout.addSpacing(15)

        # ------------------------------------------------------
        # Périodes enregistrées
        # ------------------------------------------------------

        titre_liste = QLabel("Périodes enregistrées")

        titre_liste.setStyleSheet("font-size: 18px; font-weight: bold;")

        contenu_layout.addWidget(titre_liste)

        self.liste = QListWidget()

        self.liste.setMinimumHeight(150)
        self.liste.setMaximumHeight(220)

        contenu_layout.addWidget(self.liste)

        # ------------------------------------------------------
        # Bouton supprimer
        # ------------------------------------------------------

        boutons_liste = QHBoxLayout()

        bouton_supprimer = QPushButton("Supprimer")

        bouton_supprimer.clicked.connect(self.supprimer_fermeture)

        boutons_liste.addWidget(bouton_supprimer)

        boutons_liste.addStretch()

        contenu_layout.addLayout(boutons_liste)

        # ------------------------------------------------------
        # Formulaire d'ajout
        # ------------------------------------------------------

        contenu_layout.addSpacing(15)

        titre_ajout = QLabel("Ajouter une période")

        titre_ajout.setStyleSheet("font-size: 18px; font-weight: bold;")

        contenu_layout.addWidget(titre_ajout)

        formulaire = QFormLayout()

        self.date_debut = QDateEdit()

        self.date_debut.setCalendarPopup(True)

        self.date_debut.setDate(QDate.currentDate())

        self.date_debut.setDisplayFormat("dd/MM/yyyy")

        self.date_fin = QDateEdit()

        self.date_fin.setCalendarPopup(True)

        self.date_fin.setDate(QDate.currentDate())

        self.date_fin.setDisplayFormat("dd/MM/yyyy")

        self.type_fermeture = QComboBox()

        for nom, valeur in self.TYPES.items():

            self.type_fermeture.addItem(nom, valeur)

        self.libelle = QLineEdit()

        self.libelle.setPlaceholderText("Exemple : Congé d'automne")

        formulaire.addRow("Du :", self.date_debut)

        formulaire.addRow("Au :", self.date_fin)

        formulaire.addRow("Type :", self.type_fermeture)

        formulaire.addRow("Libellé :", self.libelle)

        contenu_layout.addLayout(formulaire)

        bouton_ajouter = QPushButton("Ajouter la période")

        bouton_ajouter.clicked.connect(self.ajouter_fermeture)

        contenu_layout.addWidget(bouton_ajouter)

        contenu_layout.addStretch()

        scroll.setWidget(contenu)

        layout_principal.addWidget(scroll)

    # ==========================================================
    # LÉGENDE
    # ==========================================================

    def creer_legende(self, texte, couleur):

        label = QLabel(texte)

        label.setStyleSheet(f"""
            QLabel {{
                background-color: {couleur};
                border: 1px solid #999999;
                padding: 5px;
            }}
            """
        )

        return label

    # ==========================================================
    # NOM DES MOIS
    # ==========================================================

    def nom_mois(self, mois):

        mois_noms = [
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin",
            "Juillet",
            "Août",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre",
        ]

        return mois_noms[mois - 1]

    # ==========================================================
    # CHARGER LES PÉRIODES
    # ==========================================================

    def charger_fermetures(self):

        self.liste.clear()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                date_debut,
                date_fin,
                type,
                libelle
            FROM calendrier_fermetures
            ORDER BY date_debut
            """
        )

        resultats = cursor.fetchall()

        conn.close()

        types_inverse = {
            valeur: nom
            for nom, valeur in self.TYPES.items()
        }

        for (fermeture_id, date_debut, date_fin, type_fermeture, libelle) in resultats:

            nom_type = types_inverse.get(type_fermeture, type_fermeture)

            texte = (f"{date_debut} → {date_fin} |" f"{nom_type} | {libelle}")

            item = QListWidgetItem(texte)

            item.setData(Qt.ItemDataRole.UserRole, fermeture_id)

            self.liste.addItem(item)

    # ==========================================================
    # AJOUTER UNE PÉRIODE
    # ==========================================================

    def ajouter_fermeture(self):

        debut = self.date_debut.date()
        fin = self.date_fin.date()

        if debut > fin:
            QMessageBox.warning(self, "Dates incorrectes","La date de début doit être antérieure ou égale à la date de fin.")
            return

        libelle = self.libelle.text().strip()

        if not libelle:
            QMessageBox.warning(self, "Libellé manquant", "Veuillez saisir un libellé.")
            return

        type_fermeture = (self.type_fermeture.currentData())

        date_debut = debut.toString("yyyy-MM-dd")

        date_fin = fin.toString("yyyy-MM-dd")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO calendrier_fermetures
            (
                date_debut,
                date_fin,
                type,
                libelle
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                date_debut,
                date_fin,
                type_fermeture,
                libelle
            ),
        )

        conn.commit()
        conn.close()

        self.libelle.clear()

        self.charger_fermetures()

        self.actualiser_calendrier()

    # ==========================================================
    # SUPPRIMER UNE PÉRIODE
    # ==========================================================

    def supprimer_fermeture(self):

        item = self.liste.currentItem()

        if item is None:
            QMessageBox.information(self, "Suppression", "Sélectionne une période.")
            return

        fermeture_id = item.data(Qt.ItemDataRole.UserRole)

        confirmation = QMessageBox.question(self, "Supprimer", "Voulez-vous supprimer cette période ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM calendrier_fermetures
            WHERE id = ?
            """,
            (fermeture_id,),
        )

        conn.commit()
        conn.close()

        self.charger_fermetures()

        self.actualiser_calendrier()

    # ==========================================================
    # ACTUALISER LE CALENDRIER
    # ==========================================================

    def actualiser_calendrier(self):

        annee = self.annee.value()

        # Positionner chaque mois
        for index, calendrier in enumerate(self.calendriers):

            mois = index + 1

            calendrier.setCurrentPage(annee, mois)

            # Supprimer les anciens formats
            calendrier.setDateTextFormat(QDate(), QTextCharFormat())

        self.colorer_periodes(annee)

    # ==========================================================
    # COLORER LES PÉRIODES
    # ==========================================================

    def colorer_periodes(self, annee):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                date_debut,
                date_fin,
                type
            FROM calendrier_fermetures
            """
        )

        periodes = cursor.fetchall()

        conn.close()

        for (date_debut, date_fin, type_fermeture) in periodes:

            debut = QDate.fromString(date_debut, "yyyy-MM-dd")

            fin = QDate.fromString(date_fin, "yyyy-MM-dd")

            # La période ne concerne pas l'année affichée
            if fin.year() < annee:
                continue

            if debut.year() > annee:
                continue

            # Début d'affichage
            if debut.year() < annee:

                courant = QDate(annee, 1, 1)

            else:

                courant = debut

            # Fin d'affichage
            if fin.year() > annee:

                derniere = QDate(annee, 12, 31)

            else:

                derniere = fin

            couleur = self.COULEURS.get(type_fermeture, "#eeeeee")

            format_date = QTextCharFormat()

            format_date.setBackground(QColor(couleur))

            while courant <= derniere:

                calendrier = self.calendriers[courant.month() - 1]

                calendrier.setDateTextFormat(courant, format_date)

                courant = courant.addDays(1)


# ============================================================
# MENUS
# ============================================================

class MenusWidget(QWidget):

    MOIS = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]

    JOURS = [
        "Lundi",
        "Mardi",
        "Mercredi",
        "Jeudi",
        "Vendredi",
        "Samedi",
        "Dimanche",
    ]

    def __init__(self):
        super().__init__()

        self.creer_interface()
        self.charger_bibliotheque()
        self.charger_mois()

    # ==========================================================
    # INTERFACE
    # ==========================================================

    def creer_interface(self):

        layout = QVBoxLayout(self)

        # ------------------------------------------------------
        # Titre
        # ------------------------------------------------------

        titre = QLabel("Gestion des menus")

        titre.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout.addWidget(titre)

        # ------------------------------------------------------
        # Sélection année / mois
        # ------------------------------------------------------

        selection = QHBoxLayout()

        selection.addWidget(QLabel("Année :"))

        self.annee = QSpinBox()

        self.annee.setRange(2000, 2100)

        self.annee.setValue(QDate.currentDate().year())

        self.annee.valueChanged.connect(self.changer_mois)

        selection.addWidget(self.annee)

        selection.addSpacing(20)

        selection.addWidget(QLabel("Mois :"))

        self.mois = QComboBox()

        self.mois.addItems(self.MOIS)

        self.mois.setCurrentIndex(QDate.currentDate().month() - 1)

        self.mois.currentIndexChanged.connect(self.changer_mois)

        selection.addWidget(self.mois)

        selection.addStretch()

        layout.addLayout(selection)

        # ------------------------------------------------------
        # Tableau
        # ------------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels([
            "Date",
            "Jour",
            "Potage",
            "Plat A citoyen",
            "Plat B citoyen",
            "Plat école",
            "Dessert",
        ])

        self.table.verticalHeader().setVisible(False)

        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)

        # Largeur des colonnes
        header = self.table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        for colonne in range(2, 7):

            header.setSectionResizeMode(colonne, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # ------------------------------------------------------
        # Bouton enregistrer
        # ------------------------------------------------------

        boutons = QHBoxLayout()

        bouton_enregistrer = QPushButton("Enregistrer le mois")

        bouton_enregistrer.clicked.connect(self.enregistrer_mois)

        boutons.addWidget(bouton_enregistrer)

        boutons.addStretch()

        layout.addLayout(boutons)

    # ==========================================================
    # BIBLIOTHÈQUE
    # ==========================================================

    def charger_bibliotheque(self):

        self.potages = []
        self.plats = []
        self.desserts = []

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, nom
            FROM bibliotheque
            WHERE categorie = ?
            AND actif = 1
            ORDER BY nom COLLATE NOCASE
            """,
            ("POTAGE",)
        )

        self.potages = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, nom
            FROM bibliotheque
            WHERE categorie = ?
            AND actif = 1
            ORDER BY nom COLLATE NOCASE
            """,
            ("PLAT",)
        )

        self.plats = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, nom
            FROM bibliotheque
            WHERE categorie = ?
            AND actif = 1
            ORDER BY nom COLLATE NOCASE
            """,
            ("DESSERT",)
        )

        self.desserts = cursor.fetchall()

        conn.close()

    # ==========================================================
    # CHANGEMENT DE MOIS
    # ==========================================================

    def changer_mois(self):

        self.charger_bibliotheque()
        self.charger_mois()

    # ==========================================================
    # CRÉATION D'UNE LISTE DÉROULANTE
    # ==========================================================

    def creer_combo(self, elements):

        combo = QComboBox()

        combo.addItem("", None)

        for element_id, nom in elements:

            combo.addItem(nom, element_id)

        # ------------------------------------------------------
        # Recherche
        # ------------------------------------------------------

        combo.setEditable(True)

        champ = combo.lineEdit()

        champ.setReadOnly(False)

        champ.setPlaceholderText("Rechercher...")

        # Ne pas ajouter de nouvelles valeurs
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # ------------------------------------------------------
        # Compléteur
        # ------------------------------------------------------

        completer = QCompleter(combo.model(), combo)

        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        completer.setFilterMode(Qt.MatchFlag.MatchContains)

        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        champ.setCompleter(completer)

        return combo

    def informations_jour(self, date):

        date_sql = date.toString("yyyy-MM-dd")

        jour_semaine = date.dayOfWeek()

        # ======================================================
# DIMANCHE : PRIORITÉ À L'AFFICHAGE DU SAMEDI
# ======================================================

        if jour_semaine == 7:
            samedi = date.addDays(-1)

            return {
                "type": "DIMANCHE",
                "libelle": "Plat du samedi au choix",
                "ecole": False,
                "citoyen": True,
                "jour_reference": samedi.toString("yyyy-MM-dd"),
            }

        # ======================================================
        # CAS SPÉCIAUX : 25 DÉCEMBRE
        # ======================================================

        if date.month() == 12 and date.day() == 25:

            veille = date.addDays(-1)

            return {
                "type": "NOEL",
                "libelle": "Repas du 24 décembre au choix",
                "ecole": False,
                "citoyen": True,
                "jour_reference": veille.toString(
                    "yyyy-MM-dd"
                ),
            }

        # ======================================================
        # CAS SPÉCIAUX : 1er JANVIER
        # ======================================================

        if date.month() == 1 and date.day() == 1:

            veille = date.addDays(-1)

            return {
                "type": "NOUVEL_AN",
                "libelle": "Repas du 31 décembre au choix",
                "ecole": False,
                "citoyen": True,
                "jour_reference": veille.toString(
                    "yyyy-MM-dd"
                ),
            }

        # ======================================================
        # VÉRIFIER LES PÉRIODES ENREGISTRÉES
        # ======================================================

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT type, libelle
            FROM calendrier_fermetures
            WHERE date_debut <= ?
            AND date_fin >= ?
            LIMIT 1
            """,
            (
                date_sql,
                date_sql
            )
        )

        periode = cursor.fetchone()

        conn.close()

        # ======================================================
        # JOUR FÉRIÉ
        # ======================================================

        if periode and periode[0] == "FERIE":

            return {
                "type": "FERIE",
                "libelle": periode[1],
                "ecole": False,
                "citoyen": True,
                "jour_reference": None,
            }

        # ======================================================
        # CONGÉ SCOLAIRE
        # ======================================================

        if periode and periode[0] == "CONGE":

            return {
                "type": "CONGE",
                "libelle": periode[1],
                "ecole": False,
                "citoyen": True,
                "jour_reference": None,
            }

        # ======================================================
        # FERMETURE EXCEPTIONNELLE
        # ======================================================

        if periode and periode[0] == "FERMETURE":

            return {
                "type": "FERMETURE",
                "libelle": periode[1],
                "ecole": False,
                "citoyen": True,
                "jour_reference": None,
            }

        # ======================================================
        # DIMANCHE NORMAL
        # ======================================================

        if jour_semaine == 7:

            samedi = date.addDays(-1)

            return {
                "type": "DIMANCHE",
                "libelle": "Plat du samedi au choix",
                "ecole": False,
                "citoyen": True,
                "jour_reference": samedi.toString(
                    "yyyy-MM-dd"
                ),
            }

        # ======================================================
        # JOUR NORMAL
        # ======================================================

        ecole = jour_semaine in (
            1,  # lundi
            2,  # mardi
            4,  # jeudi
            5,  # vendredi
        )

        return {
            "type": "NORMAL",
            "libelle": "",
            "ecole": ecole,
            "citoyen": True,
            "jour_reference": None,
        }

    def date_reference_citoyen(self, date):

        date_sql = date.toString("yyyy-MM-dd")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT type
            FROM calendrier_fermetures
            WHERE date_debut <= ?
            AND date_fin >= ?
            LIMIT 1
            """,
            (
                date_sql,
                date_sql
            )
        )

        periode = cursor.fetchone()

        conn.close()

        # ======================================================
        # NOËL
        # ======================================================

        if date.month() == 12 and date.day() == 25:
            return date.addDays(-1)

        # ======================================================
        # NOUVEL AN
        # ======================================================

        if date.month() == 1 and date.day() == 1:
            return date.addDays(-1)

        # ======================================================
        # JOUR FÉRIÉ
        # ======================================================
        # Pour un citoyen, le jour férié reprend
        # systématiquement le menu de la veille.

        if periode and periode[0] == "FERIE":

            return date.addDays(-1)

    def menu_reference(self, date):

        date_reference = self.date_reference_citoyen(date)

        if date_reference is None:
            return None

        date_sql = date_reference.toString("yyyy-MM-dd")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                potage_id,
                plat_a_id,
                plat_b_id,
                dessert_id
            FROM menus
            WHERE date_menu = ?
            """,
            (date_sql,)
        )

        menu = cursor.fetchone()

        conn.close()

        return menu

    # ==========================================================
    # CHARGER LE MOIS
    # ==========================================================

    def charger_mois(self):

        annee = self.annee.value()

        mois = self.mois.currentIndex() + 1

        nombre_jours = QDate(annee, mois, 1).daysInMonth()

        self.table.setRowCount(nombre_jours)

        for jour in range(1, nombre_jours + 1):

            date = QDate(annee, mois, jour)

            date_sql = date.toString("yyyy-MM-dd")

            nom_jour = self.JOURS[date.dayOfWeek() - 1]

            infos = self.informations_jour(date)

            # ==================================================
            # DATE
            # ==================================================

            item_date = QTableWidgetItem(date.toString("dd/MM/yyyy"))

            item_date.setData(Qt.ItemDataRole.UserRole, date_sql)

            self.table.setItem(jour - 1, 0, item_date)

            # ==================================================
            # JOUR
            # ==================================================

            texte_jour = nom_jour

            if infos["type"] == "FERIE":
                texte_jour += f" - {infos['libelle']}"

            elif infos["type"] == "CONGE":
                texte_jour += f" - {infos['libelle']}"

            elif infos["type"] == "FERMETURE":
                texte_jour += f" - {infos['libelle']}"

            self.table.setItem(jour - 1, 1, QTableWidgetItem(texte_jour))

            # ==================================================
            # POTAGE
            # ==================================================

            potage = self.creer_combo(self.potages)

            self.table.setCellWidget(jour - 1, 2, potage)

            # ==================================================
            # PLAT A CITOYEN
            # ==================================================

            plat_a = self.creer_combo(self.plats)

            self.table.setCellWidget(jour - 1, 3, plat_a)

            # ==================================================
            # PLAT B CITOYEN
            # ==================================================

            plat_b = self.creer_combo(self.plats)

            self.table.setCellWidget(jour - 1, 4, plat_b)

            # ==================================================
            # PLAT ÉCOLE
            # ==================================================

            plat_ecole = self.creer_combo(self.plats)

            self.table.setCellWidget(jour - 1, 5, plat_ecole)


            # --------------------------------------------------
            # Pas de repas école
            # --------------------------------------------------

            if not infos["ecole"]:

                plat_ecole.setEnabled(False)

                plat_ecole.setStyleSheet(
                    """
                    QComboBox {
                        background-color: #e0e0e0;
                        color: #888888;
                    }

                    QComboBox::drop-down {
                        background-color: #d0d0d0;
                    }
                    """
                )

                plat_ecole.setToolTip(
                    "Pas de repas école ce jour"
                )

            # ==================================================
            # DESSERT
            # ==================================================

            dessert = self.creer_combo(self.desserts)

            self.table.setCellWidget(jour - 1, 6, dessert)

            if date.dayOfWeek() == 7:
                potage.setEnabled(False)
                plat_a.setEnabled(False)
                plat_b.setEnabled(False)
                plat_ecole.setEnabled(False)
                dessert.setEnabled(False)

                plat_a.lineEdit().setPlaceholderText("Plat du samedi au choix")

                plat_b.lineEdit().setPlaceholderText("Plat du samedi au choix")

            # ======================================================
            # JOURNÉE CITOYEN DÉRIVÉE
            # ======================================================

            date_reference = self.date_reference_citoyen(date)

            if date_reference is not None:
                menu_reference = self.menu_reference(date)

                if menu_reference is not None:

                    valeurs_reference = [
                        menu_reference[0],  # potage
                        menu_reference[1],  # plat A
                        menu_reference[2],  # plat B
                        menu_reference[3],  # dessert
                    ]

                    colonnes = [
                        2,  # potage
                        3,  # plat A
                        4,  # plat B
                        6,  # dessert
                    ]

                    for colonne, valeur in zip(colonnes, valeurs_reference):

                        combo = self.table.cellWidget(jour - 1, colonne)

                        if combo is not None:

                            index = combo.findData(valeur)

                            if index >= 0:

                                combo.setCurrentIndex(index)

                            combo.setEnabled(False)

                            combo.setStyleSheet(
                                """
                                QComboBox {
                                    background-color: #e0e0e0;
                                    color: #777777;
                                }

                                QComboBox::drop-down {
                                    background-color: #d0d0d0;
                                }
                                """
                            )

                            combo.setToolTip("Menu repris de la journée précédente")
          
        # ======================================================
        # Recharger les menus enregistrés
        # ======================================================

        self.charger_menus_existants()

        # ======================================================
        # Charger les menus références
        # ======================================================
        self.charger_menus_references()


    # ==========================================================
    # CHARGER LES MENUS EXISTANTS
    # ==========================================================

    def charger_menus_existants(self):

        annee = self.annee.value()

        mois = self.mois.currentIndex() + 1

        premier_jour = f"{annee:04d}-{mois:02d}-01"

        dernier_jour = QDate(annee, mois, 1).daysInMonth()

        dernier_jour = (f"{annee:04d}-{mois:02d}-{dernier_jour:02d}")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                date_menu,
                potage_id,
                plat_a_id,
                plat_b_id,
                plat_ecole_id,
                dessert_id
            FROM menus
            WHERE date_menu BETWEEN ? AND ?
            """,
            (
                premier_jour,
                dernier_jour
            )
        )

        menus = cursor.fetchall()

        conn.close()

        menus_dict = {
            menu[0]: menu
            for menu in menus
        }

        for ligne in range(self.table.rowCount()):

            item_date = self.table.item(ligne, 0)

            date_sql = item_date.data(Qt.ItemDataRole.UserRole)

            if date_sql not in menus_dict:
                continue

            menu = menus_dict[date_sql]

            # menu :
            # 0 date
            # 1 potage
            # 2 plat A
            # 3 plat B
            # 4 plat école
            # 5 dessert

            valeurs = [
                menu[1],
                menu[2],
                menu[3],
                menu[4],
                menu[5],
            ]

            for colonne, valeur in enumerate(valeurs, start=2):

                combo = self.table.cellWidget(ligne, colonne)

                if combo is not None:

                    index = combo.findData(valeur)

                    if index >= 0:

                        combo.setCurrentIndex(index)

    # ==========================================================
    # CHARGER LES MENUS REFERENCES
    # ==========================================================
    def charger_menus_references(self):

        for ligne in range(self.table.rowCount()):

            item_date = self.table.item(ligne, 0)

            if item_date is None:
                continue

            date_sql = item_date.data(Qt.ItemDataRole.UserRole)

            date = QDate.fromString(date_sql, "yyyy-MM-dd")

            # Seulement dimanche pour l'instant
            if date.dayOfWeek() != 7:
                continue

            menu = self.menu_reference(date)

            if menu is None:
                continue

            potage_id = menu[0]
            plat_a_id = menu[1]
            plat_b_id = menu[2]
            dessert_id = menu[3]

            # Potage
            potage = self.table.cellWidget(ligne, 2)

            if potage is not None:

                index = potage.findData(potage_id)

                if index >= 0:
                    potage.setCurrentIndex(index)

            # Dessert
            dessert = self.table.cellWidget(ligne, 6)

            if dessert is not None:
                index = dessert.findData(dessert_id)

                if index >= 0:
                    dessert.setCurrentIndex(index)

    # ==========================================================
    # ENREGISTRER LE MOIS
    # ==========================================================

    def enregistrer_mois(self):

        conn = get_connection()
        cursor = conn.cursor()

        for ligne in range(self.table.rowCount()):

            item_date = self.table.item(ligne, 0)

            date_sql = item_date.data(Qt.ItemDataRole.UserRole)

            date = QDate.fromString(date_sql, "yyyy-MM-dd")

            infos = self.informations_jour(date)

            # ======================================================
            # DIMANCHE
            # ======================================================
            # Le dimanche ne possède pas son propre menu.
            # Il utilise le menu du samedi.

            if infos["type"] == "DIMANCHE":
                continue

            # ======================================================
            # JOUR FÉRIÉ
            # ======================================================
            # Le jour férié utilise le menu de la veille.
            # Il ne crée donc pas son propre menu.

            if infos["type"] == "FERIE":
                continue

            # ======================================================
            # NOËL / NOUVEL AN
            # ======================================================

            if infos["type"] in ("NOEL", "NOUVEL_AN"):
                continue

            combos = []

            for colonne in range(2, 7):

                combo = self.table.cellWidget(ligne, colonne)

                if combo is None:
                    combos.append(None)
                else:
                    combos.append(
                        combo.currentData()
                    )

            potage_id = combos[0]
            plat_a_id = combos[1]
            plat_b_id = combos[2]
            plat_ecole_id = combos[3]
            dessert_id = combos[4]

            # Vérifier si la journée existe déjà
            cursor.execute(
                """
                SELECT id
                FROM menus
                WHERE date_menu = ?
                """,
                (date_sql,)
            )

            existant = cursor.fetchone()

            if existant:

                cursor.execute(
                    """
                    UPDATE menus
                    SET
                        potage_id = ?,
                        plat_a_id = ?,
                        plat_b_id = ?,
                        plat_ecole_id = ?,
                        dessert_id = ?
                    WHERE date_menu = ?
                    """,
                    (
                        potage_id,
                        plat_a_id,
                        plat_b_id,
                        plat_ecole_id,
                        dessert_id,
                        date_sql
                    )
                )

            else:

                # Ne créer une ligne que si quelque
                # chose a été encodé
                if any(valeur is not None for valeur in combos):

                    cursor.execute(
                        """
                        INSERT INTO menus
                        (
                            date_menu,
                            potage_id,
                            plat_a_id,
                            plat_b_id,
                            plat_ecole_id,
                            dessert_id
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            date_sql,
                            potage_id,
                            plat_a_id,
                            plat_b_id,
                            plat_ecole_id,
                            dessert_id
                        )
                    )

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Enregistrement", "Le mois a été enregistré.")

        self.charger_mois()


# ============================================================
# PARAMÈTRES
# ============================================================

class ParametresWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Paramètres")

        titre.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout.addWidget(titre)
        layout.addStretch()


# ============================================================
# FENÊTRE PRINCIPALE
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Gestion des menus")

        self.resize(1200, 700)

        self.tabs = QTabWidget()

        # --------------------------------------------------
        # Création des différentes pages
        # --------------------------------------------------

        self.menus_widget = MenusWidget()

        self.bibliotheque_widget = BibliothequeWidget()

        self.calendrier_widget = CalendrierWidget()

        self.parametres_widget = ParametresWidget()

        # --------------------------------------------------
        # Ajout des onglets
        # --------------------------------------------------

        self.tabs.addTab(self.menus_widget, "Menus")

        self.tabs.addTab(self.bibliotheque_widget, "Bibliothèque")

        self.tabs.addTab( self.calendrier_widget, "Calendrier")

        self.tabs.addTab(self.parametres_widget, "Paramètres")

        # --------------------------------------------------
        # Détection du changement d'onglet
        # --------------------------------------------------

        self.tabs.currentChanged.connect(self.changement_onglet)

        self.setCentralWidget(self.tabs)

    def changement_onglet(self, index):

        widget = self.tabs.widget(index)

        if widget is self.menus_widget:

            # Recharger la bibliothèque
            self.menus_widget.charger_bibliotheque()

            # Recharger le mois actuellement affiché
            self.menus_widget.charger_mois()

# ============================================================
# PROGRAMME
# ============================================================

def main():

    create_database()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()