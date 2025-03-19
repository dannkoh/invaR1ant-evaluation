(declare-const in0 Int)
(declare-const target Int)

(assert (and (not ( = target 0)) (not ( = ( -  target in0) 0))))

(check-sat)
(get-model)