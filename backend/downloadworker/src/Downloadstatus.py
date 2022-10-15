from enum import IntEnum

class Downloadstatus(IntEnum):
    DEFAULT = 0
    PROCESSING = 102 # We are trying to download this atm
    SEEN = 1 # We have seen this url in responses, but did not save any of it
    INCOMPLETE = 206 # We have seen this url in responses and saved what was available, but could fetch again for more info
    DOWNLOADED = 200 # We have downloaded the tweet from this url
    BLOCKED = 403 # The user whose token this request used was blocked from viewing this content
    NONEXISTING = 404 # This id does not exist on twitter
    GONE = 410 # This tweet existed, but does not anymore (probably deleted)
    LOCKED = 423 # This tweet is currently locked (but maybe only temporarily)
    ILLEGAL = 451 #

    def is_better_than(self, other) -> bool:
        if self == other:
            return False
        if Downloadstatus.DOWNLOADED in [self,other]: # Download is better than every other status
            return self == Downloadstatus.DOWNLOADED
        if Downloadstatus.INCOMPLETE in [self,other]: # Incomplete is better than every remaining status
            return self == Downloadstatus.INCOMPLETE
        if Downloadstatus.SEEN in [self,other]: # Seen is worse than every remaining status,
                                                # since they each contain more information
            return other == Downloadstatus.SEEN
        return False # For now, the rest is not differentiated, we could rank them in the future.
