(declare-const in6 Int)
(declare-const in5 Int)
(declare-const in0 Int)
(declare-const in2 Int)
(declare-const in1 Int)
(declare-const in4 Int)
(declare-const in3 Int)

(assert (and (and (and (and (and (and (and (and (and (and (and (and (and (not ( = in0 65))  ( ==  in0 66)) (not ( = in1 69)))  ( ==  in1 70)) (not ( = in2 73))) (not ( = in2 74))) (not ( = in3 65)))  ( ==  in3 66)) (not ( = in4 69)))  ( ==  in4 70)) (not ( = in5 73))) (not ( = in5 74))) (not ( = in6 65)))  ( ==  in6 66)))

(check-sat)
(get-model)