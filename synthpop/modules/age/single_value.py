""" A single value age distribution """

__all__ = ["SingleValue", ]
__author__ = "S. Johnson"
__date__ = "2022-07-06"
__license__ = "GPLv3"
__version__ = "1.0.0"


import numpy as np
from ._age import Age


class SingleValue(Age):
    """
    SingleAge subclass of Age base class. This subclass is for Populations that
    have age characterized by a single age value. 

    Attributes
    ----------
    age_func_name : str
        name of the Age subclass set to single_value.
    age_value : float [Gyr]
        The value of the age all stars in this Population are assumed to have
        in Giga-years.

    Methods
    -------
    __init__(self,**kwargs) : None
        initialize the Age class
    draw_random_age(self,  N: int or None = None) :  ndarray or float  [Gyr]
        returns one or more values for the age of a star in giga-years. This function is
        specified by population.age_func_name.
    average_age(self) : float [Gyr]
        returns the average age of the distribution in giga-years.
    """

    def __init__(self, age_value: float, **kwargs):
        super().__init__(**kwargs)
        self.age_func_name = 'single_value'
        self.age_value = age_value

    def draw_random_age(self, N: int or None = None) -> np.ndarray or float:
        """
        Generate a "random" age from a single value distribution

        Parameters
        ----------
        N : int, None, optional
            if N is set to an integer, an array with N random ages is returned

        Returns
        -------
        age : float, ndarray [Gyr]
            single age or numpy array of N ages in Giga-years
        """
        if N is None:
            return self.age_value
        else:
            return np.ones(N) * self.age_value

    def average_age(self) -> float:
        """Determine the average age of the population"""
        return self.age_value

    def get_maximum_age(self) -> float:
        """
        returns the maximum age generated by the distribution
        """
        return self.age_value