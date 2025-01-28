from duck.exceptions.all import PortError


class PortRecorder:
    """
    Class to record all ports that will be of use within Duck entire life cycle.
    """

    OCCUPIED_PORTS: dict[int, str] = {}
    """Dict of occupied ports mapping to their occupiers"""

    @classmethod
    def add_new_occupied_port(cls, port: int, occupier: str):
        """
        Adds new port as an occupied port (already in use port).
        """
        if port not in cls.OCCUPIED_PORTS.keys():
            cls.OCCUPIED_PORTS.update({port: occupier})
        else:
            raise PortError(
                f'Port conflict with port "{port}", port already in use. Port occupied by "{cls.OCCUPIED_PORTS.get(port)}"'
            )
