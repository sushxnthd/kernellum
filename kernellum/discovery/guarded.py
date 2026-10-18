"""Exploratory bounded reconstruction after the failed external confirmation.

The observed range is a heuristic, not a physical bound. This can bias legitimate
extrapolation. LOO validation recomputes bounds excluding each held-out label.
"""
import numpy as np
from .representation import RepresentationBank

class GuardedRepresentationBank(RepresentationBank):
    margin=.1
    def fit(self,observed,values):
        super().fit(observed,values)
        low=float(self.y.min());high=float(self.y.max());span=high-low
        self.bounds=(low-self.margin*span,high+self.margin*span)
        n=len(self.y)
        lo=np.array([np.min(np.delete(self.y,i)) for i in range(n)])
        hi=np.array([np.max(np.delete(self.y,i)) for i in range(n)])
        span=hi-lo
        for model in self.models:
            loo=self.y-self.yscale*model['error']
            loo=np.clip(loo,lo-self.margin*span,hi+self.margin*span)
            model['error']=(self.y-loo)/self.yscale
            model['original_cv']=float(np.mean(model['error']**2))
        self.models.sort(key=lambda model:model['original_cv'])
        return self
    def predict_model(self,model,x):
        return np.clip(super().predict_model(model,x),*self.bounds)
