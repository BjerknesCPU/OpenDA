#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for letting a Python script use the Java object SimulationKwadraticCostFunction which is included in OpenDA.
Every function below setup() uses global variables calculated by setup(), so when using this module
it is recomended that setup() is called first.
Created on Wed Oct 10 14:39:10 2018

@author: hegeman
"""

import os
from py4j.java_gateway import JavaGateway

import py_openda.utils.py4j_utils as utils

gateway = JavaGateway()   # connect to the JVM

#os.chdir('/v3/Stage/Rick/openda/openda_public/py_openda/examples/py_swan_calibration')
scriptdir = os.getcwd()
#scriptdir = '/v3/Stage/Rick/openda/openda_public/py_openda/examples/py_swan_calibration'








class Kwadratic:
    
    def __init__(self):
        
        #Initialize the model factory
        #model_input_dir = "/Users/nils/Develop/py4j/swanModel/config"
        model_input_dir = os.path.join(scriptdir, 'swanModel', 'config')
        model_config_xml = "swanStochModelConfig.xml"
    
    
        model_factory = gateway.jvm.org.openda.model_swan.SwanCalibStochModelFactory()
        utils.initialize_openda_configurable(model_factory, model_input_dir, model_config_xml)
    
        #Initialize stoch observer
        #observer_input_dir = "/Users/nils/Develop/py4j/stochObserver"
        observer_input_dir = model_input_dir = os.path.join(scriptdir, 'stochObserver')
        observer_config_xml = "swanStochObsConfig.xml"
    
        observer = gateway.jvm.org.openda.observers.IoObjectStochObserver()
        utils.initialize_openda_configurable(observer, observer_input_dir, observer_config_xml)
        
        
        #Initialize cost function org.openda.algorithms
        self.cost_function = gateway.jvm.org.openda.algorithms.SimulationKwadraticCostFunction(model_factory, observer)
    
        #Get initial parameter
        outputLevel = gateway.jvm.org.openda.interfaces.IStochModelFactory.OutputLevel.Debug
        self.model_instance = model_factory.getInstance(outputLevel)
        selectionTimes = self.model_instance.getTimeHorizon()
        self.selection = observer.createSelection(selectionTimes)
        self.target_time = self.model_instance.getTimeHorizon().getEndTime()

    def get_parameters(self):
        """
        Setup the OpenDA model factory, stoch observer and object function
    
        :return: a tuple containing an instance of the cost function, the initial parameters, an instance of the model and a stoch observer
        """
    
    
        p = self.model_instance.getParameters()        
        return p
    
    def get_obs(self):
        """
        Find the observations and corresponding uncertainties at the relevant locations 
        
        :return: a tuple containing a list of the mean of all observations at each locations, followed by their respective standard deviations
        """
        
        obs_mean = self.selection.getExpectations()
        obs_mean = utils.input_to_py_list(obs_mean.getValues())
        obs_std = self.selection.getStandardDeviations()
        obs_std = utils.input_to_py_list(obs_std.getValues())
        
        return (obs_mean, obs_std)
    
    def object_function(self, p):
        """
        Compute the predictions of the object function for parameters p
        :param p: parameters
        :return: list of predictions
        """
    
        # Create an OpenDA TreeVector with parameter value
        p_new = utils.input_to_j_vector(p)
        model_new = self.model_instance
        model_new.setParameters(p_new)
        model_new.compute(self.target_time)
    
        descr = self.selection.getObservationDescriptions()
        prd = model_new.getObservationOperator().getObservedValues(descr)
        prd = utils.input_to_py_list(prd.getValues())
    
        val = self.cost_function.evaluate(p_new, "-")
        print("Cost="+str(val)+" p="+str(p))
        return prd