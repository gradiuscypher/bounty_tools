# Wrapper class for bountytools DB interaction
from database import database
from database.database import db_session
from database.models import Host, Althosts


class BountyToolsDb:
    def __init__(self):
        database.init_db()
        self.session = db_session()

    def add_host(self, ip_address, hostname, source, workspace):
        qresult = self.session.query(Host).filter(Host.ip_address == ip_address)
        if qresult.count() > 0:
            first_host = qresult.first()

            # Check to see if the first_host has althosts that match, to avoid dupes
            fh_alts = self.session.query(Althosts).filter(Althosts.host_id == first_host.id).filter(Althosts.hostname == hostname)
            if fh_alts.count() == 0 and (first_host.host != hostname):
                ah = Althosts(hostname=hostname, source=source, host=first_host)
                self.session.add(ah)
                self.session.commit()
                return True

            else:
                return False

        # If no other IP exists
        else:
            h = Host(host=hostname, ip_address=ip_address, source=source, workspace=workspace)
            self.session.add(h)
            self.session.commit()
            return True

