class Maillon:
    def __init__(self, data):
        self.data = data  
        self.next = None  

class ListeDeCourse:
    def __init__(self):
        self.head = None 

    def insererAuDebut(self, data):
        new_maillon = Maillon(data) 
        new_maillon.next = self.head 
        self.head = new_maillon      

    def afficher(self):
        temp = self.head
        while temp is not None:
            print(temp.data, end=" -> ")
            temp = temp.next
        print("None")

    def supprimerPremier(self):
        if self.head is not None:
            self.head = self.head.next
            
    def supprimerDernier(self):
        if self.head is None:
            return
        if self.head.next is None:
            self.head = None
            return
        temp = self.head
        while temp.next.next is not None:
            temp = temp.next
        temp.next = None

liste = ListeDeCourse()
liste.insererAuDebut("Pommes")
liste.insererAuDebut("Bananes")
liste.insererAuDebut("Carottes")
liste.afficher()