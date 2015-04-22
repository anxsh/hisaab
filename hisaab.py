#!/usr/bin/python

import sys
import yaml
import argparse
from operator import itemgetter

columns = 100

def do_hisaab(expenses):
	persons = expenses['persons']
	group_map = expenses['groups']
	
	person_group = {}
	groups = []
	for group_id, group_members in group_map.items():
		groups.append(group_id)
		for member in group_members:
			person_group[member] = group_id
	
	for person in persons:
		if person not in person_group:
			groups.append(person)
			person_group[person] = person
	
	total_amount = 0.0
	debit = {}
	credit = {}
	for person in persons:
		debit[person_group[person]] = 0.0
		credit[person_group[person]] = 0.0

	print 'Expenses: '
	print '=' * columns
	
	# formatting 
	max_item_length = 0
	max_group_length  = 0
	for expense in expenses['expenses']:
		if (len(expense['item']) > max_item_length):
			max_item_length = len(expense['item'])
	for group in groups:
		if(len(group) > max_group_length):
			max_group_length = len(group)
			
	for expense in expenses['expenses']:

		if 'amount' not in expense:
			print 'amount missing in expense (%s)' % (expense)
			sys.exit(1)
		if 'payer' not in expense:
			print 'payer missing in expense (%s)' % (expense)
			sys.exit(1)
		payer = expense['payer']
		amount = float(expense['amount'])

		if payer not in persons:
			print 'unknown payer %s' % (payer)
			sys.exit(1)

		exclude = []
		if 'exclude' in expense:
			exclude = expense['exclude']

		num_sharers = len(persons) - len(exclude)
		per_person_amount = amount / num_sharers
		if exclude:
			print '%s:  total ($%4d), each ($%5.2f), sharers: all but {%s}, paid by %s' % (expense['item'].ljust(max_item_length+2), amount, per_person_amount, ", ".join(exclude), payer)
		else:
			print '%s:  total ($%4d), each ($%5.2f), sharers: all, paid by %s' % (expense['item'].ljust(max_item_length+2), amount, per_person_amount, payer)

		credit[person_group[payer]] += amount
		for person in persons:
			if person not in exclude:
				debit[person_group[person]] += per_person_amount

	print '\nExpense by group: '
	print '=' * columns	
	for group in groups:
		print '%s:  $%d' % (group.ljust(max_group_length+2), debit[group])

	init_delta = {}
	total_owed = 0.0
	for group in groups:
		init_delta[group] = credit[group] - debit[group]
		if init_delta[group] > 0:
			total_owed += init_delta[group]
		# print 'delta: %s => %d (%d, %d)' % (person, init_delta[person], credit[person], debit[person]) 

	print "\nSuggested distribution: "
	print '=' * columns
	distribution = {}
	while total_owed > 1: # $1 is a low enough filter
		delta = {}
		
		for group in groups:
			d = credit[group] - debit[group]
			if abs(d) > 1:
				delta[group] = d
		delta = sorted(delta.items(), key=itemgetter(1))

		(low, high) = [delta[i] for i in [0, -1]]
		(payer, payer_amount) = low
		(payee, payee_amount) = high
		assert(payee_amount > 0)
		assert(payer_amount < 0)

		payout = min(abs(payee_amount), abs(payer_amount))

		total_owed -= payout
 		credit[payee] -= payout
		debit[payer] -= payout
		
		# print delta
		# print "%s pays %s => $%d: %d" % (payer, payee, payout, total_owed)		
		print "%s pays %s => $%d" % (payer.ljust(max_group_length+2), payee, payout)		
		
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Do the hisaab')
	parser.add_argument('-c', 
						'--config', 
						dest='file', 
						help='yaml configuration file containing expenses', 
						required=True)
	config = vars(parser.parse_args())
	expenses = yaml.load(file(config['file'], 'rb').read())
	do_hisaab(expenses)