import pandas as pd 
import re
from pathlib import Path 

class StructuredStore:

    def __init__(self, kb_path : str):
        self.kb_path = Path(kb_path)
        print("KB Path:", self.kb_path.resolve())
        
        self.employees = pd.read_csv(self.kb_path/ "structured" / "employee_directory.csv")
        self.tickets = pd.read_csv(self.kb_path/ "structured" / "jira_export.csv")

        #Safety Normalization
        self.employees.fillna("",inplace=True)
        self.tickets.fillna("",inplace=True)
    
    #-------Employee Methods-------

    def get_employee_by_name(self, name:str):
        return self.employees[self.employees["name"].str.lower() == name.lower()]

    def get_direct_reports(self, manager_name:str):
        manager = self.get_employee_by_name(manager_name)
        if manager.empty:
            return pd.DataFrame()
        
        manager_id = manager.iloc[0]["employee_id"]
        return self.employees[self.employees["manager"] == manager_id]
    
    def get_team_members(self, team:str):
        return self.employees[self.employees["team"].str.lower() == team.lower()]

    #-------Ticket Methods-------

    def get_ticket_by_id(self, ticket_id:str):
        return self.tickets[self.tickets["ticket_id"] == ticket_id] 
    
    def get_tickets_by_team(self, team:str):
        return self.tickets[self.tickets["team"].str.lower() == team.lower()]

    def get_tickets_by_employee(self, employee_name:str):
        return self.tickets[self.tickets["assignee"].str.lower() == employee_name.lower()]

    def get_tickets_by_product(self, product:str):
        return self.tickets[self.tickets["related_product"].str.lower() == product.lower()]

    def get_critical_tickets(self):
        return self.tickets[self.tickets["priority"].str.lower() == "critical"]

    def get_blocked_tickets(self):
        return self.tickets[self.tickets["dependencies"].str.contains("Blocked by", case=False, na=False)]

    def get_ticket_dependencies(self, ticket_id: str):
        ticket = self.get_ticket_by_id(ticket_id)
        if ticket.empty:
            return []

        dep_text = ticket.iloc[0]["dependencies"]

        if not dep_text:
            return []

        return re.findall(r"TECH-\d+", dep_text)

    def get_tickets_by_priority(self, priority:str):
        return self.tickets[self.tickets["priority"].str.lower() == priority.lower()]

