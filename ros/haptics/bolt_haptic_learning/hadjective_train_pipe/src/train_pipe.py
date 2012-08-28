#!/usr/bin/env python
import roslib; roslib.load_manifest("hadjective_train_pipe")
import rospy
import numpy as np
import sys 
import os
from optparse import OptionParser
import cPickle
import pickle
import bolt_learning_utilities as utilities
import extract_features as extract_features
import matplotlib.pyplot as plt 
import sklearn.decomposition

from bolt_feature_obj import BoltFeatureObj
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics import classification_report
from sklearn.datasets.samples_generator import make_blobs
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.cross_validation import cross_val_score
from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
from sklearn import cross_validation
from sklearn import preprocessing



# Loads the data from h5 table and adds labels
# Returns the dictionary of objects
def loadDataFromH5File(input_file, adjective_file):
   
    # Takes the input h5 file and converts into bolt object data
    all_bolt_data = utilities.convertH5ToBoltObjFile(input_file, None, False);
   
    # Inserts adjectives into the bolt_data  
    all_bolt_data_adj = utilities.insertAdjectiveLabels(all_bolt_data, "all_objects_majority4.pkl", adjective_file, True)

    return all_bolt_data_adj


# Takes the bolt data and extracts features to run
def BoltMotionObjToFeatureObj(all_bolt_data):
    """
    Pull out PCA components from all data

    For each object - pull out features and store in feature_obj
    with the same structure as all_bolt_data
   
        Dictionary - "tap", "slide", "slow_slide", 
                     "thermal_hold", "squeeze"

    """
    # DO PCA Calculations here 
    
    # Store in feature class object
    all_features_obj_dict = dict();

    for motion_name in all_bolt_data:
        trial_list = all_bolt_data.get(motion_name)
        print motion_name

        feature_list = list()
        # For all objects
        for trial in trial_list:
            
            bolt_feature_obj = extract_features.extract_features(trial)
            
            feature_list.append(bolt_feature_obj)

        # Store all of the objects away
        all_features_obj_dict[motion_name] = feature_list
            
    return all_features_obj_dict        
    

def bolt_obj_2_feature_vector(all_features_obj_dict, feature_name_list):
    """
    Pull out PCA components from all data

    For each object - pull out features and store in feature_obj
    with the same structure as all_bolt_data
   
        Dictionary - "tap", "slide", "slow_slide", 
                     "thermal_hold", "squeeze"

    Directly store the features into a vector
    See createFeatureVector for more details on structure

    """
    
    # DO PCA Calculations here 
     


    # Store in feature class object
    all_features_vector_dict = dict()
    
    # Store labels
    for motion_name in all_features_obj_dict:
        
        feature_obj_list = all_features_obj_dict.get(motion_name)

        all_adjective_labels_dict = dict()
        feature_vector_list = list()

        # For all objects
        for bolt_feature_obj in feature_obj_list:

            # Create feature vector
            feature_vector = utilities.createFeatureVector(bolt_feature_obj, feature_name_list) 
            feature_vector_list.append(feature_vector)

            # Create label dictionary
            labels = bolt_feature_obj.labels
            for adjective in labels:
                # Check if it is the first time adjective added
                if (all_adjective_labels_dict.has_key(adjective)):
                    adjective_array = all_adjective_labels_dict[adjective]
                else:
                    adjective_array = list()
                
                # Store array
                adjective_array.append(labels[adjective])
                all_adjective_labels_dict[adjective] = adjective_array

        # Store all of the objects away
        all_features_vector_dict[motion_name] = np.array(feature_vector_list)
        
    
    return (all_features_vector_dict, all_adjective_labels_dict)      


def run_dbscan(input_vector, num_clusters):
    """
    run_dbscan - expects a vector of features and the number of
                 clusters to generate

                 dbscan uses nearest neighbor metrics to compute
                 similarity

    Returns the populated clusters
    """


def run_kmeans(input_vector, num_clusters, obj_data):
    """
    run_kmeans - expects a vector of features and the number of
                 clusters to generate

    Returns the populated clusters 
    """
    k_means = KMeans(init='k-means++', n_clusters=num_clusters, n_init=100)

    k_means.fit(input_vector)
    k_means_labels = k_means.labels_
    k_means_cluster_centers = k_means.cluster_centers_
    k_mean_labels_unique = np.unique(k_means_labels)

    # Pull clusters out
    clusters = dict()
    cluster_names = dict()
    cluster_ids = dict()
    cluster_all_adjectives = dict()
    # Get a list of all adjectives
    adjectives = obj_data[0].labels.keys()

    
    for labels in k_mean_labels_unique:
        idx = np.nonzero(k_means_labels == labels)
        clusters[labels] = [obj_data[i] for i in idx[0]]
        cluster_names[labels] = [obj.name for obj in clusters[labels]]
        cluster_ids[labels] = [obj.object_id for obj in clusters[labels]]
   
    for adj in adjectives:
        cluster_adj = dict()
        for labels in k_mean_labels_unique:
            cluster_adj[labels] = [obj.labels[adj] for obj in clusters[labels]] 
        
        cluster_all_adjectives[adj] = cluster_adj

    #import pdb; pdb.set_trace() 
    
    return (k_means_labels, k_means_cluster_centers, clusters)

def true_false_results(predicted_labels, true_labels):
 
    FP = (predicted_labels - true_labels).tolist().count(1)
    FN = (predicted_labels - true_labels).tolist().count(-1)
    TP = (predicted_labels & true_labels).tolist().count(1)
    TN = ((predicted_labels | true_labels) ^ True).tolist().count(1)


    return(TP, TN, FP, FN)


def matthews_corr_coef(TP,TN,FP,FN):

    try:
        MCC = (TP*TN - FP*FN)/(np.sqrt(((TP+FP)*(TP+FN)*(TN+FP)*(TN+FN))))
    except:
        MCC = (TP*TN - FP*FN)/1

    return (MCC)


def train_knn(train_vector, train_labels, test_vector, test_labels):
    """
    train_knn - expects a vector of features and a nx1 set of
                corresponding labels.  Finally the number of
                neighbors used for comparison

    Returns a trained knn classifier
    """
    
    # Data scaling
    train_vector_scaled = preprocessing.scale(train_vector)
    test_vector_scaled = preprocessing.scale(test_vector)

    # Grid search with nested cross-validation
    parameters = [{'n_neighbors': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]}]
    knn = GridSearchCV(KNeighborsClassifier(), parameters, score_func=f1_score, cv=5)
    knn.fit(train_vector_scaled, train_labels)
    score = knn.grid_scores_
    knn_best = knn.best_estimator_
    report = classification_report(test_labels, knn.predict(test_vector_scaled))

    import pdb; pdb.set_trace()
    pass

    #print report
    return (knn_best, score, report)



def train_svm(train_vector, train_labels, test_vector, test_labels):
    """
    train_svm - expects a vector of features and a nx1 set of
                corresponding labels

    Returns a trained SVM classifier
    """
    
    # Data scaling
    train_vector_scaled = preprocessing.scale(train_vector)
    test_vector_scaled = preprocessing.scale(test_vector)
    
    # Grid search with nested cross-validation
    parameters = {'kernel': ['rbf'], 'C': [1, 1e1, 1e2, 1e3, 1e4], 'gamma': [1, 1e-1, 1e-2, 1e-3, 1e-4]}
    #parameters = {'kernel': ['poly'], 'C': [1, 1e1, 1e2, 1e3, 1e4], 'gamma': [1, 1e-1, 1e-2, 1e-3, 1e-4]} 
    svm = GridSearchCV(SVC(), parameters, score_func=f1_score, cv=8)
    svm.fit(train_vector_scaled, train_labels)
    score = svm.grid_scores_
    report = classification_report(test_labels, svc.predict(test_vector_scaled))

    import pdb; pdb.set_trace()
    pass

    return (svm, score, report)


def single_train(feature_vector, labels):
    """
    single_train - expects a vector of features and an nx1 set of
                   corresponding labels to train a single classifier
                   on 1 motion

    Returns trained KNN and SVM classifiers that have been optimized
    using grid search
    """

    # Split data
    train_vector, test_vector, train_labels, test_labels = train_test_split(feature_vector, labels, test_size=0.25)

    # Run KNN
    knn, knn_score, knn_report = train_knn(train_vector, train_labels, test_vector, test_labels)
    print "Ran KNN"

    # Run SVM
    svm, svm_score, svm_report = train_svm(train_vector, train_labels, test_vector, test_labels)
    print "Ran SVM"


    return(knn, knn_report, svm_report)


def full_train(all_data, train_feature_vector, adjective_dictionary):
    

    
    # Fun full training
    report_file_knn = open("Full_KNN_preprocess_reports.txt", "a")
    report_file_svm = open("Full_SVM_reports.txt", "a")
    
    all_knn_classifiers = dict()
    all_knn_scores = dict()
    all_knn_reports = dict()
    all_svm_classifiers = dict()
    all_svm_scores = dict()
    all_svm_reports = dict()
   
    adjectives = adjective_dictionary.keys()
    

    """
    # Run KNN
    for adj in adjectives:
        knn_classifiers = dict()
        knn_scores = dict()
        knn_reports = dict()
        
        pkl_file_name = adj.replace("'",'"')
        pkl_file_suffix = "_knn.pkl"
        pkl_file_name += pkl_file_suffix
         
        for motion_name in all_data:
            print "Training KNN classifier with adjective %s, phase %s \n" %(adj, motion_name)
            knn, score, report = train_knn(train_feature_vector[motion_name], train_adjective_dictionary[adj], test_feature_vector[motion_name], test_adjective_dictionary[adj])
            knn_classifiers[motion_name] = knn
            knn_scores[motion_name] = score
            knn_reports[motion_name] = report

            # Store the report into a text file
            report_file_knn.write('Adjective: ')
            report_file_knn.write(adj)
            report_file_knn.write('    Motion name: ')
            report_file_knn.write(motion_name)
            report_file_knn.write('\nKNN report\n')
            report_file_knn.write(report)
            report_file_knn.write('\n\n')
 
 
        # When trainings for a certain adjective with all five motions are done, save this classifier
        #cPickle.dump(knn_classifiers, open(pkl_file_name, "w"), cPickle.HIGHEST_PROTOCOL)
        #print "The KNN classifier for adjective %s is stored as %s " %(adj, pkl_file_name)
 
        del pkl_file_name
 
        all_knn_classifiers[adj] = knn_classifiers
        all_knn_scores[adj] = knn_scores
        all_knn_reports[adj] = knn_reports
 
        print "Ran KNN for adjective %s" %(adj)
 
     print "Ran KNN"

     """   

        # Run SVM
 
    for adj in adjectives:
        svm_classifiers = dict()
        svm_scores = dict()
        svm_reports = dict()
         
        pkl_file_name = adj.replace("'",'"')
        pkl_file_suffix = "_svm.pkl"
        pkl_file_name += pkl_file_suffix
         
 
        #import pdb;pdb.set_trace()     
        #pass
 
        for  motion_name in all_data:
             print "Training SVM classifier with adjective %s, phase %s \n" %(adj, motion_name)
             svm_classifiers = dict()
             svm_scores = dict()
             svm_reports = dict()
 
             svm, score, report = train_svm(train_feature_vector[motion_name], train_adjective_dictionary[adj], test_feature_vector[motion_name], test_adjective_dictionary[adj])
             svm_classifiers[adj] = svm
             svm_scores[adj] = score
             svm_reports[adj] = report
 
              
             # Store the report into a text file
             report_file_svm.write('Adjective: ')
             report_file_svm.write(adj)
             report_file_svm.write('    Motion name: ')
             report_file_svm.write(motion_name)
             report_file_svm.write('\nSVM report\n')
             report_file_svm.write(report)
             report_file_svm.write('\n\n')
  
        # When trainings for a certain adjective with all five motions are done, save this classifier
        # cPickle.dump(svm_classifiers, open(pkl_file_name, "w"), cPickle.HIGHEST_PROTOCOL)
        # print "The SVM classifier for adjective %s is stored as %s " %(adj, pkl_file_name)
        # del pkl_file_name

        all_svm_classifiers[adj] = svm_classifiers
        all_svm_scores[adj] = svm_scores
        all_svm_reports[adj] = svm_reports
         
        print "Ran SVM for adjective %s" %(adj)

    print "Ran SVM"



# MAIN FUNCTION
def main(input_file, adjective_file, train_feature_pkl, test_feature_plk):


    # Load data into the pipeline. First check
    # for feature object pkl files
    print "Loading data from file"
    if train_feature_pkl == None or test_feature_pkl == None:
        # If no features, load data from either an
        # h5 and adjective file or directly from
        # a saved pkl file
        if input_file.endswith(".h5"):
            all_data = loadDataFromH5File(input_file, adjective_file)
        else:
            all_data = utilities.loadBoltObjFile(input_file)

        print "loaded data"

    
        # Split the data into train and test
        train_data, test_data = utilities.split_data(all_data, 0.9)
        
        # Convert motion objects into feature objects
        train_all_features_obj_dict = BoltMotionObjToFeatureObj(train_data)
        test_all_features_obj_dict = BoltMotionObjToFeatureObj(test_data)
        file_ptr = open("train_feature_objs.pkl","w")
        cPickle.dump(train_all_features_obj_dict, file_ptr, cPickle.HIGHEST_PROTOCOL)
        file_ptr.close()
        file_ptr = open("test_feature_objs.pkl","w")
        cPickle.dump(test_all_features_obj_dict, file_ptr, cPickle.HIGHEST_PROTOCOL)

    else:
        # Load the saved feature object pkl files
        file_ptr = open(train_feature_pkl,"r")
        train_all_features_obj_dict = cPickle.load(file_ptr)
        file_ptr.close()
        file_ptr = open(test_feature_pkl,"r")
        test_all_features_obj_dict = cPickle.load(file_ptr)
        file_ptr.close()

        print "loaded data"

    # Take loaded data and extract out features
    feature_name_list = ["pdc_rise_count", "pdc_area", "pdc_max", "pac_energy", "pac_sc", "pac_sv", "pac_ss", "pac_sk", "tac_area", "tdc_exp_fit"]




    # Pull desired features from feature objects
    train_feature_vector, train_adjective_dictionary = bolt_obj_2_feature_vector(train_all_features_obj_dict, feature_name_list)
    test_feature_vector, test_adjective_dictionary = bolt_obj_2_feature_vector(test_all_features_obj_dict, feature_name_list)


    
    # Preprocess the train and test vectors by scaling
    for motion_name in train_feature_vector:
        train_feature_vector[motion_name] = preprocessing.scale(train_feature_vector[motion_name])
        test_feature_vector[motion_name] = preprocessing.scale(test_feature_vector[motion_name])

    print "Features are scaled"

    print("Created feature vector containing %s" % feature_name_list)

    


    motion = 'squeeze'    
    adjective = 'sticky'
    knn_classifiers, knn_report, svm_report = single_train(train_feature_vector[motion_name], train_adjective_dictionary[adjective])

    pkl_file_name = adjective.replace("'",'"')
    pkl_file_suffix = ".pkl"
    pkl_file_name += pkl_file_suffix

    cPickle.dump(knn_classifiers, open(pkl_file_name, "w"), cPickle.HIGHEST_PROTOCOL)

 
    report_file.write('Motion name: ')
    report_file.write(motion_name)
    report_file.write('\nAdjective: ')
    report_file.write(adjective)
    report_file.write('\nKNN report\n')
    report_file.write(knn_report)
    report_file.write('\nSVM report\n')
    report_file.write(svm_report)
    report_file.write('\n\n')

    report_file.close()

    # Run full train
    full_train(all_data, train_feature_vector, train_adjective_dictionary)



    
    """   
    # Run KNN
    for adj in adjectives:
	knn_classifiers = dict()
        knn_scores = dict()
        knn_reports = dict()
       
        pkl_file_name = adj.replace("'",'"')
        pkl_file_suffix = "_knn.pkl"
	pkl_file_name += pkl_file_suffix
	

	#import pdb;pdb.set_trace() 	
	#pass

	for  motion_name in all_data:
   	     print "Training KNN classifier with adjective %s, phase %s \n" %(adj, motion_name)
	     knn, score, report = train_knn(train_feature_vector[motion_name], train_adjective_dictionary[adj], test_feature_vector[motion_name], test_adjective_dictionary[adj])
             knn_classifiers[motion_name] = knn
             knn_scores[motion_name] = score
	     knn_reports[motion_name] = report
             
	     # Store the report into a text file
             report_file_knn.write('Adjective: ')
             report_file_knn.write(adj)
	     report_file_knn.write('    Motion name: ')
    	     report_file_knn.write(motion_name)
    	     report_file_knn.write('\nKNN report\n')
	     report_file_knn.write(report)
	     report_file_knn.write('\n\n')

        import pdb;pdb.set_trace()
        pass	

        # When trainings for a certain adjective with all five motions are done, save this classifier
        cPickle.dump(knn_classifiers, open(pkl_file_name, "w"), cPickle.HIGHEST_PROTOCOL)
        print "The KNN classifier for adjective %s is stored as %s " %(adj, pkl_file_name)
         
        del pkl_file_name
              
        all_knn_classifiers[adj] = knn_classifiers
        all_knn_scores[adj] = knn_scores
        all_knn_reports[adj] = knn_reports

        print "Ran KNN for adjective %s" %(adj)
        #import pdb;pdb.set_trace()
        #pass

    print "Ran KNN"
    """

    """
    # Run SVM

    for adj in adjectives:
        svm_classifiers = dict()
        svm_scores = dict()
        svm_reports = dict()
        
        pkl_file_name = adj.replace("'",'"')
        pkl_file_suffix = "_svm.pkl"
        pkl_file_name += pkl_file_suffix
        

        #import pdb;pdb.set_trace()     
        #pass

        for  motion_name in all_data:
             print "Training SVM classifier with adjective %s, phase %s \n" %(adj, motion_name)
	     svm_classifiers = dict()
             svm_scores = dict()
             svm_reports = dict()

             svm, score, report = train_svm(train_feature_vector[motion_name], train_adjective_dictionary[adj], test_feature_vector[motion_name], test_adjective_dictionary[adj])
             svm_classifiers[adj] = svm
             svm_scores[adj] = score
             svm_reports[adj] = report

             
	     # Store the report into a text file
             report_file_svm.write('Adjective: ')
             report_file_svm.write(adj)
             report_file_svm.write('    Motion name: ')
             report_file_svm.write(motion_name)
             report_file_svm.write('\nSVM report\n')
             report_file_svm.write(report)
             report_file_svm.write('\n\n')

        import pdb;pdb.set_trace()     
        pass
 
        # When trainings for a certain adjective with all five motions are done, save this classifier
        cPickle.dump(svm_classifiers, open(pkl_file_name, "w"), cPickle.HIGHEST_PROTOCOL)
        print "The SVM classifier for adjective %s is stored as %s " %(adj, pkl_file_name)
        del pkl_file_name

        all_svm_classifiers[adj] = svm_classifiers
        all_svm_scores[adj] = svm_scores
        all_svm_reports[adj] = svm_reports
        
        print "Ran SVM for adjective %s" %(adj)

        #import pdb;pdb.set_trace()
        #pass

    print "Ran SVM"
    """

 

# Parse the command line arguments
def parse_arguments():
    """
    Parses the arguments provided at command line.
    
    Returns:
    (input_file, adjective_file, range)
    """
    parser = OptionParser()
    parser.add_option("-i", "--input_file", action="store", type="string", dest = "in_h5_file")
    parser.add_option("-o", "--output", action="store", type="string", dest = "out_file", default = None) 
    parser.add_option("-a", "--input_adjective", action="store", type="string", dest = "in_adjective_file")
    parser.add_option("-n", "--input_train_feature_pkl", action="store", type="string", dest = "in_train_feature_pkl", default = None)
    parser.add_option("-s", "--input_test_feature_pkl", action="store", type="string", dest = "in_test_feature_pkl", default = None)

    (options, args) = parser.parse_args()
    input_file = options.in_h5_file #this is required
   
    if options.out_file is None:
        (_, name) = os.path.split(input_file)
        name = name.split(".")[0]
        out_file = name + ".pkl"
    else:    
        out_file = options.out_file
        if len(out_file.split(".")) == 1:
            out_file = out_file + ".pkl"
    
    adjective_file = options.in_adjective_file

    train_feature_pkl = options.in_train_feature_pkl
    test_feature_pkl = options.in_test_feature_pkl

    return input_file, out_file, adjective_file, train_feature_pkl, test_feature_pkl


if __name__ == "__main__":
    input_file, out_file, adjective_file, train_feature_pkl, test_feature_pkl = parse_arguments()
    main(input_file, adjective_file, train_feature_pkl, test_feature_pkl)
