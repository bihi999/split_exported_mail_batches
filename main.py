import openpyxl
import re
import pandas as pd
import os
import shutil
from typing import List, Dict, Set

from classes import mail
from classes.csvfile import CSVHandler


from korpus import ausgeschieden_korpus01


mapping_dataframes = { "abgleich_dwh": {
                                "absender": None,
                                "webid": lambda x: pd.to_numeric(x, errors="coerce").astype("Int64"),
                                "webfirmenid": lambda x: pd.to_numeric(x, errors="coerce").astype("Int64"),
                            }
                        }


#------Auslagern in die Hilfsfunktionen
def leere_ordner(pfad):
    # Überprüfe, ob der Pfad tatsächlich existiert und ein Verzeichnis ist
    if os.path.exists(pfad) and os.path.isdir(pfad):
        # Iteriere über alle Dateien und Unterordner im Verzeichnis
        for dateiname in os.listdir(pfad):
            dateipfad = os.path.join(pfad, dateiname)
            try:
                # Wenn es ein Unterordner ist, benutze shutil.rmtree um den Ordner und alle seine Inhalte zu löschen
                if os.path.isdir(dateipfad):
                    shutil.rmtree(dateipfad)
                # Wenn es eine Datei ist, benutze os.remove um die Datei zu löschen
                else:
                    os.remove(dateipfad)
            except Exception as e:
                print(f"Fehler beim Löschen von {dateipfad}: {e}")
    else:
        print("Gegebener Pfad ist kein Verzeichnis oder existiert nicht")



if __name__ == "__main__":
    filepath_mails = 'C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\dage-358_03042026_18.CSV'  
    filepath_dwh_ergebnisse = 'C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\dwh_abgleich_30032026.csv'
    ordnerpfad_einstufungen = 'C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\thematische_zuordnungen_kontrolltabelle'
    ordnerpfad_einstufungen_tabellen = 'C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\thematische_zuordnungen'
    ordnerpfad_referenzen = "C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\output.xlsx"

#---------a_ Baue einen Handler für die Umgebung: Ordnerpfade einlesen - Abfragen ob löschen - Ordnerpfade zur Verfügung stellen - Exceptions sammeln
#---------h_ Die Schreibfunktionen der Klassen kennen diese Funktion nicht und damit bestehen aktuelle und ältere Ergebnislisten nebeneinander
#---------h_ Exceptions von leere_ordner() laufen ins Leere - Funktionen erhalten im Exception-Fall keine alternativen Pfade
    leere_ordner(ordnerpfad_einstufungen)
    leere_ordner(ordnerpfad_einstufungen_tabellen)

    
#----------------h_ Sehr aufwendige Umsetzung - Zusammenfassung
#----------------h_ Exception-Handling unbefriedigend - sauber über Klassenattribut .exceptions handhaben und vereinheitlichen

    result = CSVHandler.validate_file(filepath_mails)
    if not result.is_valid:
        print("Fehler Dateipfad Mailexport:", result.errors)
    else:
        csv_mail_handler = CSVHandler.from_file(filepath_mails)
        print(len(csv_mail_handler.content))

    
    result = CSVHandler.validate_file(filepath_dwh_ergebnisse)
    if not result.is_valid:
        print("Fehler Dateipfad DWH_Ergebnisse:", result.errors)
    else:
        csv_dwh_handler = CSVHandler.from_file(filepath_dwh_ergebnisse)
        df_dwh_results = csv_dwh_handler.csv_to_pandas(",")
        if not isinstance(df_dwh_results, pd.DataFrame):
            print("CSV ließt sich nicht als DataFrame einlesen: {}".format(df_dwh_results))
        else:
            df_dwh_results = csv_dwh_handler.transform_pandas(df_dwh_results, mapping_dataframes, "abgleich_dwh")
            if not isinstance(df_dwh_results, pd.DataFrame):
                print("Erstellter DataFrame ließ sich nicht korrekt transformieren: {}".format(df_dwh_results))


#----------------------------------Neuer Ablauf Split-and-Rule

    splitted_mails, report_splitting = csv_mail_handler.split_content([r'"\n"', r'","'])
    print(report_splitting)

    #-----Ausgabe zur Kontrolle ersetzen - Report liefert die Info: Wurde erwartete Anzahl von Daten eingelesen und ist Anzahl auf Level 2 wie erwartet ein Vielfaches von 3 (Elementen)
    #for mail_entry in splitted_mails:
     #   print("\n")
      #  if len(mail_entry) != 3:
       #     print("Eintrag mit unerwarteter Länge.")
        #    continue
        #else:
        #    for field in mail_entry:
        #        print(field[:10])
            
    mail_dict = mail.DictForMail.from_raw_data(splitted_mails)
    
    for absender, mailinstanz in mail_dict._items.items():
        mailinstanz.satztrenner()
        mailinstanz.themen_ermitteln_schlagworte(ausgeschieden_korpus01.themen_schlagworte)
        
    
    mail_dict.print_thematische_zuordnungen()
    mail_dict.export_thematische_zuordnungen_to_excel(ordnerpfad_einstufungen)

    mail_dict.export_mails_to_excel(ordnerpfad_einstufungen_tabellen)


    for absender, mailinstanz in mail_dict._items.items():
        mailinstanz.referenzen_ermitteln()

    mail_dict.export_references_to_excel(ordnerpfad_referenzen, show_dataframe=True)
        



    if False:

        csv_content = read_csv_as_string(file_path)
        
        # Definieren Sie die Regex-Muster nach Bedarf
        first_split_regex = r'"\n"'  # Beispiel-Regex zum ersten Teilen
        second_split_regex = r'","'  # Beispiel-Regex zum zweiten Teilen
        
        # Aufteilen des CSV-Inhalts
        parts = split_string(csv_content, first_split_regex)
        
        # Erstellen des Dictionaries mit Mail-Instanzen
        mails_dict = process_mail_parts(parts, second_split_regex)
        
        # Anwenden der Satztrennungsfunktion auf jede Mail-Instanz
        for mail in mails_dict.values():
            mail.satztrenner()
            # mail.satztrenner_deutsch() # Deaktiviert für diesen Schritt
            mail.themen_ermitteln_schlagworte(themen_schlagworte, verbose=False)
        
        # Einlesen und Umwandeln der DWH-CSV-Datei in ein Dictionary
        filepath_dwh_ergebnisse = 'C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\dwh_abgleich_25032026.csv'
        results_dict_dwh_abgleich  = csv_to_dict(filepath_dwh_ergebnisse, delimiter=",")

        # Abgleich der Mail-Instanzen mit den DWH-Daten
        abgleich_mails_dwh(mails_dict, results_dict_dwh_abgleich)
        
        # Exportieren der Mails in Excel-Tabellen
        leere_ordner('C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\thematische_zuordnungen')
        export_mails_to_excel(mails_dict, 'C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\thematische_zuordnungen')

        # Ausgabe der thematischen Zuordnungen
        print_thematische_zuordnungen(mails_dict)

        # Ausgabe der thematischen Zuordnungen als Excel-Tabelle
        leere_ordner('C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\thematische_zuordnungen_kontrolltabelle')
        export_thematische_zuordnungen_to_excel(mails_dict, 'C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\thematische_zuordnungen_kontrolltabelle')

        referenzen_liste_gekuerzt = []
        
        for mail in mails_dict.values():
            mail.referenzen_ermitteln()
            referenzen_liste_gekuerzt.extend(mail.referenzen_umgebung_ausgeben(context_len=80))

        referenzen_liste = []
        
        for mail in mails_dict.values():
            if mail.referenzen:
                for referenz in mail.referenzen:
                    if referenz.lower() != mail.absender.lower():
                        referenzen_liste.append({"absender" : mail.absender,
                                                "referenz" : referenz,
                                                "text" : mail.text})

        referenzen_dict = pd.DataFrame(referenzen_liste)
        referenzen_dict.to_excel("C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\output.xlsx", index=False)

        referenzen_dict_gekuerzt = pd.DataFrame(referenzen_liste_gekuerzt)
        referenzen_dict_gekuerzt["text"] = referenzen_dict_gekuerzt["text"].str.replace(r"\r?\n", " ", regex=True)
        referenzen_dict_gekuerzt.to_excel("C:\\Users\\BirgerHildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\chatgpt_skripte\\DAGE-358\\output_gekuerzt.xlsx", index=False)

