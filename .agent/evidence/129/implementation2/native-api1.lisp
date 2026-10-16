;;;; Source2 qualification of exported built-ins, actual signatures and context.
(declaim (optimize (debug 3) (speed 0)))
(dolist (name '("TOP-FRAME" "FRAME-DOWN" "FRAME-DEBUG-FUN" "DEBUG-FUN-NAME"))
  (multiple-value-bind (symbol status) (find-symbol name :sb-di)
    (format t "API ~A ~S fbound=~S~%" name status (and symbol (fboundp symbol)))
    (assert (and (eq status :external) (fboundp symbol)))))
(define-condition source129-native-condition (error) ())
(declaim (notinline source129-native-frame))
(defun source129-native-frame ()
  (restart-case (error 'source129-native-condition)
    (source129-native-restart () :report "Native healthy active restart" :unused)))
(let ((observed nil))
  (catch 'observed
    (handler-bind
        ((source129-native-condition
           (lambda (condition)
             (let* ((names (loop for frame = (sb-di:top-frame) then (sb-di:frame-down frame)
                                 while frame for count below 32
                                 collect (sb-di:debug-fun-name (sb-di:frame-debug-fun frame))))
                    (restarts (mapcar #'restart-name (compute-restarts condition))))
               (format t "CONDITION ~S~%FRAMES ~S~%RESTARTS ~S~%" (type-of condition) names restarts)
               (assert (eq (type-of condition) 'source129-native-condition))
               (assert (member 'source129-native-frame names))
               (assert (member 'source129-native-restart restarts))
               (setf observed t)
               (throw 'observed nil)))))
      (source129-native-frame)))
  (assert observed))
(format t "PASS exported-sb-di-signatures-and-pre-unwind-context~%")
