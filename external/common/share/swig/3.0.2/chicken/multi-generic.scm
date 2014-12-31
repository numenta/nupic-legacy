;; This file is no longer necessary with Chicken versions above 1.92
;; 
;; This file overrides two functions inside TinyCLOS to provide support
;; for multi-argument generics.  There are many ways of linking this file
;; into your code... all that needs to happen is this file must be
;; executed after loading TinyCLOS but before any SWIG modules are loaded
;;
;; something like the following
;; (require 'tinyclos)
;; (load "multi-generic")
;; (declare (uses swigmod))
;;
;; An alternative to loading this scheme code directly is to add a
;; (declare (unit multi-generic)) to the top of this file, and then
;; compile this into the final executable or something.  Or compile
;; this into an extension.

;; Lastly, to override TinyCLOS method creation, two functions are
;; overridden: see the end of this file for which two are overridden.
;; You might want to remove those two lines and then exert more control over
;; which functions are used when.

;; Comments, bugs, suggestions: send either to chicken-users@nongnu.org or to
;; Most code copied from TinyCLOS

(define <multi-generic> (make <entity-class>
			  'name "multi-generic"
			  'direct-supers (list <generic>)
			  'direct-slots '()))

(letrec ([applicable?
          (lambda (c arg)
            (memq c (class-cpl (class-of arg))))]

         [more-specific?
          (lambda (c1 c2 arg)
            (memq c2 (memq c1 (class-cpl (class-of arg)))))]

         [filter-in
           (lambda (f l)
             (if (null? l)
                 '()
                 (let ([h (##sys#slot l 0)]
	               [r (##sys#slot l 1)] )
	           (if (f h)
	               (cons h (filter-in f r))
	               (filter-in f r) ) ) ) )])

(add-method compute-apply-generic
  (make-method (list <multi-generic>)
    (lambda (call-next-method generic)
      (lambda args
		(let ([cam (let ([x (compute-apply-methods generic)]
				 [y ((compute-methods generic) args)] )
			     (lambda (args) (x y args)) ) ] )
		  (cam args) ) ) ) ) )



(add-method compute-methods
  (make-method (list <multi-generic>)
    (lambda (call-next-method generic)
      (lambda (args)
	(let ([applicable
	       (filter-in (lambda (method)
                            (let check-applicable ([list1 (method-specializers method)]
                                                   [list2 args])
                              (cond ((null? list1) #t)
                                    ((null? list2) #f)
                                    (else
                                      (and (applicable? (##sys#slot list1 0) (##sys#slot list2 0))
                                           (check-applicable (##sys#slot list1 1) (##sys#slot list2 1)))))))
			  (generic-methods generic) ) ] )
	  (if (or (null? applicable) (null? (##sys#slot applicable 1))) 
	      applicable
	      (let ([cmms (compute-method-more-specific? generic)])
		(sort applicable (lambda (m1 m2) (cmms m1 m2 args))) ) ) ) ) ) ) )

(add-method compute-method-more-specific?
  (make-method (list <multi-generic>)
    (lambda (call-next-method generic)
      (lambda (m1 m2 args)
	(let loop ((specls1 (method-specializers m1))
		   (specls2 (method-specializers m2))
		   (args args))
	  (cond-expand
	   [unsafe
	    (let ((c1  (##sys#slot specls1 0))
		  (c2  (##sys#slot specls2 0))
		  (arg (##sys#slot args 0)))
	      (if (eq? c1 c2)
		  (loop (##sys#slot specls1 1)
			(##sys#slot specls2 1)
			(##sys#slot args 1))
		  (more-specific? c1 c2 arg))) ] 
	   [else
	    (cond ((and (null? specls1) (null? specls2))
		   (##sys#error "two methods are equally specific" generic))
		  ;((or (null? specls1) (null? specls2))
		  ; (##sys#error "two methods have different number of specializers" generic))
                  ((null? specls1) #f)
                  ((null? specls2) #t)
		  ((null? args)
		   (##sys#error "fewer arguments than specializers" generic))
		  (else
		   (let ((c1  (##sys#slot specls1 0))
			 (c2  (##sys#slot specls2 0))
			 (arg (##sys#slot args 0)))
		     (if (eq? c1 c2)
			 (loop (##sys#slot specls1 1)
			       (##sys#slot specls2 1)
			       (##sys#slot args 1))
			 (more-specific? c1 c2 arg)))) ) ] ) ) ) ) ) )

) ;; end of letrec

(define multi-add-method
  (lambda (generic method)
    (slot-set!
     generic
     'methods
       (let filter-in-method ([methods (slot-ref generic 'methods)])
         (if (null? methods)
           (list method)
           (let ([l1 (length (method-specializers method))]
		 [l2 (length (method-specializers (##sys#slot methods 0)))])
             (cond ((> l1 l2)
                    (cons (##sys#slot methods 0) (filter-in-method (##sys#slot methods 1))))
                   ((< l1 l2)
                    (cons method methods))
                   (else
                     (let check-method ([ms1 (method-specializers method)]
                                        [ms2 (method-specializers (##sys#slot methods 0))])
                       (cond ((and (null? ms1) (null? ms2))
                              (cons method (##sys#slot methods 1))) ;; skip the method already in the generic
                             ((eq? (##sys#slot ms1 0) (##sys#slot ms2 0))
                              (check-method (##sys#slot ms1 1) (##sys#slot ms2 1)))
                             (else
                               (cons (##sys#slot methods 0) (filter-in-method (##sys#slot methods 1))))))))))))

    (##sys#setslot (##sys#slot generic (- (##sys#size generic) 2)) 1 (compute-apply-generic generic)) ))

(define (multi-add-global-method val sym specializers proc)
  (let ((generic (if (procedure? val) val (make <multi-generic> 'name (##sys#symbol->string sym)))))
    (multi-add-method generic (make-method specializers proc))
    generic))

;; Might want to remove these, or perhaps do something like
;; (define old-add-method ##tinyclos#add-method)
;; and then you can switch between creating multi-generics and TinyCLOS generics.
(set! ##tinyclos#add-method multi-add-method)
(set! ##tinyclos#add-global-method multi-add-global-method)
