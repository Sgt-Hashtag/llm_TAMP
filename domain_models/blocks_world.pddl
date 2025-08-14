;; domain_models/blocks_world.pddl
;; Classic Blocks World Domain for AI Planning

(define (domain blocks)
  (:requirements :strips)
  
  ;; Predicates define the state space
  (:predicates 
    (on ?x ?y)        ; block ?x is on block ?y
    (ontable ?x)      ; block ?x is on the table
    (clear ?x)        ; block ?x has nothing on top of it
    (handempty)       ; the robot hand is empty
    (holding ?x)      ; the robot is holding block ?x
  )

  ;; Pick up a block from the table
  (:action pickup
    :parameters (?x)
    :precondition (and 
      (clear ?x)      ; block must be clear
      (ontable ?x)    ; block must be on table
      (handempty)     ; hand must be empty
    )
    :effect (and 
      (not (ontable ?x))   ; block no longer on table
      (not (clear ?x))     ; block no longer clear (being held)
      (not (handempty))    ; hand no longer empty
      (holding ?x)         ; now holding the block
    )
  )

  ;; Put down a block onto the table
  (:action putdown
    :parameters (?x)
    :precondition (holding ?x)  ; must be holding the block
    :effect (and 
      (not (holding ?x))   ; no longer holding block
      (clear ?x)           ; block becomes clear
      (handempty)          ; hand becomes empty
      (ontable ?x)         ; block is now on table
    )
  )
                
  ;; Stack one block on top of another
  (:action stack
    :parameters (?x ?y)
    :precondition (and 
      (holding ?x)    ; must be holding block ?x
      (clear ?y)      ; target block ?y must be clear
    )
    :effect (and 
      (not (holding ?x))   ; no longer holding ?x
      (not (clear ?y))     ; ?y no longer clear
      (clear ?x)           ; ?x becomes clear (on top)
      (handempty)          ; hand becomes empty
      (on ?x ?y)           ; ?x is now on ?y
    )
  )
                
  ;; Unstack a block from another block
  (:action unstack
    :parameters (?x ?y)
    :precondition (and 
      (on ?x ?y)      ; ?x must be on ?y
      (clear ?x)      ; ?x must be clear
      (handempty)     ; hand must be empty
    )
    :effect (and 
      (holding ?x)         ; now holding ?x
      (clear ?y)           ; ?y becomes clear
      (not (clear ?x))     ; ?x no longer clear
      (not (handempty))    ; hand no longer empty
      (not (on ?x ?y))     ; ?x no longer on ?y
    )
  )
)