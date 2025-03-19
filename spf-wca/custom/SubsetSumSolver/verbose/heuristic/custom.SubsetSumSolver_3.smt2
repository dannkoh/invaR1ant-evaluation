(declare-const in0 Int)
(declare-const in2 Int)
(declare-const in1 Int)
(declare-const target Int)

(assert (and (and (and (and (and (and (and (not ( = target 0)) (not ( = ( -  target in2) 0))) (not ( = ( -  target in1) 0))) (not ( = ( -  ( -  target in1) in2) 0))) (not ( = ( -  target in0) 0))) (not ( = ( -  ( -  target in0) in2) 0))) (not ( = ( -  ( -  target in0) in1) 0))) (not ( = ( -  ( -  ( -  target in0) in1) in2) 0))))

(check-sat)
(get-model)