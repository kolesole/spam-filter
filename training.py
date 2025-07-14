import random
from filter import MyFilter
from test_filter import CORPUS_LIST, compute_quality_for_corpus, product
from weights import get_weights, format_weights_from_dict
import copy

pretrained_filters = []
for corpus in CORPUS_LIST:
    f = MyFilter()
    f.train(corpus)
    pretrained_filters.append(f)
weights = pretrained_filters[0].weights

def evaluate(individual:dict):
    qualities = []
    for filter, corpus in product(pretrained_filters, CORPUS_LIST):
        filter.test(corpus, individual)
        qualities.append(compute_quality_for_corpus(corpus))
    quality = sum(qualities) / len(qualities)
    print(f"Q: {quality}")
    return quality

def mutate(individual):
    for key in individual:
        mutation_amount = random.uniform(-0.1, 0.1)
        individual[key] += mutation_amount
        # Clamping the value to ensure it's within a valid range (e.g., 0 to 1)
        individual[key] = max(0, min(individual[key], 1))

def crossover(parent1, parent2):
    child = {}
    for key in parent1:
        if random.random() < 0.5:
            child[key] = copy.deepcopy(parent1[key])
        else:
            child[key] = copy.deepcopy(parent2[key])
    return child

def genetic_optimization(weights, population_size=100, generations=1000):
    population = [dict(weights) for _ in range(population_size)]
    fitness_cache = {}

    for generation in range(generations):
        print(f" --- evaluating {generation}. generation --- ")
        
        # Evaluate or retrieve cached fitness for individuals
        for index, individual in enumerate(population):
            key = tuple(sorted(individual.items()))  # Creating a hashable representation of the dictionary
            if key not in fitness_cache:
                fitness_cache[key] = evaluate(individual)
        

        # Selection
        sorted_population = sorted(population, key=lambda ind: fitness_cache[tuple(sorted(ind.items()))], reverse=True)
        evaluation_of_the_best = evaluate(sorted_population[0])
        print(f'\n\nBest quality found yet: {evaluation_of_the_best}')
        # saving new best weights to file
        format_weights_from_dict(sorted_population[0], comment=f'Quality: {evaluation_of_the_best}')
        print('Quality was saved to a file.\n\n')
        population = sorted_population[:int(0.5 * len(sorted_population))]  # Keep the top 50%

        # Crossover and mutation
        while len(population) < population_size:
            parent1, parent2 = random.sample(population, 2)
            child = crossover(parent1, parent2)
            mutate(child)
            population.append(child)

    # Return the best individual
    best_individual = max(population, key=lambda ind: fitness_cache[tuple(sorted(ind.items()))])
    return best_individual


optimized_weights = genetic_optimization(weights)
print("Optimized Weights:", optimized_weights)
