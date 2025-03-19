(declare-const in0 Int)
(declare-const in1 Int)
(declare-const target Int)

(assert (and (and (and (not ( = target 0)) (not ( = ( -  target in1) 0))) (not ( = ( -  target in0) 0))) (not ( = ( -  ( -  target in0) in1) 0))))

(check-sat)
(get-model)